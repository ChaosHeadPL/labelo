from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.db import SessionDep, init_db
from app.render.layout import export_svg_pages, layout_labels_to_pages
from app.render.svg_renderer import render_label_svg
from app.schemas import (LabelBatchRequest, LabelSingleRequest,
                         PrintMissingResponse, SheetListResponse,
                         StorageCreate, StorageLabelCreate, StorageLabelOut,
                         StorageOut, TypeListResponse)
from app.services.icons import IconResolver
from app.services.sheets import SHEETS, get_sheet_by_key
from app.services.storage import (add_label_to_storage, create_storage,
                                  list_storage_labels, list_storages,
                                  mark_printed, print_missing_labels)
from app.services.templates import TEMPLATES, get_template_by_key

app = FastAPI(title="Labelo API", version="0.1.0")

# CORS for easy local testing / future UI usage
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Icon resolver expects Tabler SVGs in assets/tabler-icons
icon_resolver = IconResolver(base_dir="assets/tabler-icons")


@app.on_event("startup")
async def on_startup():
    await init_db()


@app.get("/health")
async def health():
    return {"status": "ok"}


# ---- Meta: types & sheets -----------------------------------------------------

@app.get("/types", response_model=TypeListResponse)
async def list_types():
    return {"types": list(TEMPLATES.values())}


@app.get("/sheets", response_model=SheetListResponse)
async def list_sheets():
    return {"sheets": list(SHEETS.values())}


# ---- Rendering: batch & single -----------------------------------------------

@app.post("/labels/batch")
async def generate_labels_batch(
    payload: LabelBatchRequest,
    fmt: str = Query("pdf", pattern="^(pdf|png|zip)$"),
    preview: bool = Query(False),
):
    """Generate a batch of labels and lay them out onto a sheet."""
    tpl = get_template_by_key(payload.type)
    if not tpl:
        raise HTTPException(status_code=400, detail=f"Unknown type: {payload.type}")

    sheet_key = payload.options.sheet or "A4"
    sheet = get_sheet_by_key(sheet_key)
    if not sheet:
        raise HTTPException(status_code=400, detail=f"Unknown sheet: {payload.options.sheet}")

    if len(payload.items) > 100:
        raise HTTPException(status_code=413, detail="Max 100 items per request")

    warnings: list[str] = []

    # Render per-label SVGs
    label_svgs: list[tuple[str, float, float]] = []
    for item in payload.items:
        svg, w_mm, h_mm, item_warn = render_label_svg(
            item=item,
            template=tpl,
            icon_resolver=icon_resolver,
            colors=payload.options.colors_dict(),
            padding_mm=payload.options.padding_mm or 3.0,
            outline_icons=True,
        )
        if item_warn:
            warnings.extend(item_warn)
        label_svgs.append((svg, w_mm, h_mm))

    # Layout onto pages
    pages = layout_labels_to_pages(
        label_svgs=label_svgs,
        sheet=sheet,
        with_cut_marks=payload.options.with_cut_marks or False,
    )

    # Export
    content, media_type, filename = export_svg_pages(
        pages=pages,
        fmt=fmt,
        dpi=payload.options.dpi or 300,
        pdf_title="labels",
    )

    headers = {"Content-Disposition": f"inline; filename={filename}"}
    if warnings:
        headers["X-Warnings"] = "; ".join(warnings)[:2000]

    return Response(content=content, media_type=media_type, headers=headers)


@app.post("/labels/single")
async def generate_label_single(
    payload: LabelSingleRequest,
    fmt: str = Query("pdf", pattern="^(pdf|png)$"),
):
    """Generate a single label as PDF/PNG (vector PDF; PNG at given DPI)."""
    tpl = get_template_by_key(payload.type)
    if not tpl:
        raise HTTPException(status_code=400, detail=f"Unknown type: {payload.type}")

    svg, w_mm, h_mm, warnings = render_label_svg(
        item=payload.item,
        template=tpl,
        icon_resolver=icon_resolver,
        colors=payload.options.colors_dict(),
        padding_mm=payload.options.padding_mm or 3.0,
        outline_icons=True,
    )

    content, media_type, filename = export_svg_pages(
        pages=[{"svg": svg, "width_mm": w_mm, "height_mm": h_mm}],
        fmt=fmt,
        dpi=payload.options.dpi or 300,
        pdf_title="label",
    )

    headers = {"Content-Disposition": f"inline; filename={filename}"}
    if warnings:
        headers["X-Warnings"] = "; ".join(warnings)[:2000]
    return Response(content=content, media_type=media_type, headers=headers)


# ---- Storage (pantry/workshop) ------------------------------------------------

@app.post("/storages", response_model=StorageOut)
async def api_create_storage(
    data: StorageCreate,
    session: SessionDep,
):
    return await create_storage(session, data)


@app.get("/storages", response_model=list[StorageOut])
async def api_list_storages(
    session: SessionDep,
):
    return await list_storages(session)


@app.post("/storages/{storage_id}/labels", response_model=StorageLabelOut)
async def api_add_label(
    storage_id: int,
    data: StorageLabelCreate,
    session: SessionDep,
):
    return await add_label_to_storage(session, storage_id, data)


@app.get("/storages/{storage_id}/labels", response_model=list[StorageLabelOut])
async def api_list_labels(
    storage_id: int,
    session: SessionDep,
):
    return await list_storage_labels(session, storage_id)


@app.post("/storages/{storage_id}/labels/{label_id}/printed", response_model=StorageLabelOut)
async def api_mark_printed(
    storage_id: int,
    label_id: int,
    session: SessionDep,
    qty: int = Query(1, ge=0),
):
    """Increase printed quantity for a label by `qty` (can be 0)."""
    return await mark_printed(session, storage_id, label_id, qty)


@app.post("/storages/{storage_id}/print-missing", response_model=PrintMissingResponse)
async def api_print_missing(
    storage_id: int,
    session: SessionDep,
    fmt: str = Query("pdf", pattern="^(pdf|png|zip)$"),
):
    """
    Collect labels with missing quantities for a storage and render a batch.
    If there are no missing labels, return a JSON message.
    """
    payload, warnings = await print_missing_labels(session, storage_id)
    if not payload.items:
        return JSONResponse({"message": "No missing labels", "warnings": warnings or []})

    # Resolve sheet and render (reuse the same pipeline as /labels/batch)
    sheet = get_sheet_by_key(payload.options.sheet or "A4")
    if not sheet:
        raise HTTPException(status_code=400, detail=f"Unknown sheet: {payload.options.sheet}")

    label_svgs: list[tuple[str, float, float]] = []
    all_warnings: list[str] = warnings or []

    for item in payload.items:
        # Allow per-item template override via meta.type
        tpl_key = (item.get("meta") or {}).get("type", payload.type)
        tpl = get_template_by_key(tpl_key)
        if not tpl:
            all_warnings.append(f"unknown_type:{tpl_key}")
            continue

        svg, w_mm, h_mm, w = render_label_svg(
            item=item,  # dict compatible with LabelItem used inside renderer
            template=tpl,
            icon_resolver=icon_resolver,
            colors=payload.options.colors_dict(),
            padding_mm=payload.options.padding_mm or 3.0,
            outline_icons=True,
        )
        if w:
            all_warnings.extend(w)
        label_svgs.append((svg, w_mm, h_mm))

    if not label_svgs:
        return JSONResponse({"message": "No renderable labels", "warnings": all_warnings})

    pages = layout_labels_to_pages(
        label_svgs=label_svgs,
        sheet=sheet,
        with_cut_marks=payload.options.with_cut_marks or False,
    )

    content, media_type, filename = export_svg_pages(
        pages=pages,
        fmt=fmt,
        dpi=payload.options.dpi or 300,
        pdf_title=f"storage-{storage_id}-missing",
    )

    headers = {"Content-Disposition": f"inline; filename={filename}"}
    if all_warnings:
        headers["X-Warnings"] = "; ".join(all_warnings)[:2000]
    return Response(content=content, media_type=media_type, headers=headers)
