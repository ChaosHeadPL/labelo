from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (add_label_db, create_storage_db, list_labels_db,
                      list_storages_db, mark_printed_db)
from app.schemas import (LabelBatchRequest, RenderOptions, StorageCreate,
                         StorageLabelCreate, StorageLabelOut, StorageOut)


async def create_storage(session: AsyncSession, data: StorageCreate) -> StorageOut:
    st = await create_storage_db(session, data)
    return StorageOut.model_validate(st)

async def list_storages(session: AsyncSession):
    out = [StorageOut.model_validate(s) for s in await list_storages_db(session)]
    return out

async def add_label_to_storage(session: AsyncSession, storage_id: int, data: StorageLabelCreate) -> StorageLabelOut:
    try:
        lb = await add_label_db(session, storage_id, data)
    except ValueError:
        raise HTTPException(status_code=404, detail="Storage not found")
    return StorageLabelOut.model_validate(lb)

async def list_storage_labels(session: AsyncSession, storage_id: int):
    lbs = await list_labels_db(session, storage_id)
    return [StorageLabelOut.model_validate(x) for x in lbs]

async def mark_printed(session: AsyncSession, storage_id: int, label_id: int, qty: int):
    try:
        lb = await mark_printed_db(session, storage_id, label_id, qty)
    except ValueError:
        raise HTTPException(status_code=404, detail="Label not found")
    return StorageLabelOut.model_validate(lb)

async def print_missing_labels(session: AsyncSession, storage_id: int):
    lbs = await list_labels_db(session, storage_id)
    missing = [lb for lb in lbs if lb.missing_qty > 0]
    items = []
    warnings = []
    for lb in missing:
        for _ in range(lb.missing_qty):
            items.append({
                "title": lb.title,
                "text": lb.text,
                "icon": lb.icon,
                "meta": {"type": lb.template_type, "storage_id": storage_id, "label_id": lb.id}
            })
    payload = LabelBatchRequest(
        type=missing[0].template_type if missing else "jar_label_small",
        items=items,
        options=RenderOptions()
    )
    return payload, warnings
