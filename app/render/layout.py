from io import BytesIO
from typing import List, Tuple
from zipfile import ZipFile

import cairosvg

from app.schemas import SheetDef


def mm_to_px(mm: float, dpi: int) -> float:
    return (mm / 25.4) * dpi


def layout_labels_to_pages(label_svgs: List[tuple[str, float, float]], sheet: SheetDef, with_cut_marks: bool = False):
    pages = []
    cols, rows = sheet.cols, sheet.rows
    idx = 0
    while idx < len(label_svgs):
        # budujemy jedną stronę SVG A4
        page_svg = _empty_page_svg(sheet)
        items_on_page = 0
        for r in range(rows):
            for c in range(cols):
                if idx >= len(label_svgs):
                    break
                svg, w_mm, h_mm = label_svgs[idx]
                x = sheet.margin_left_mm + c * (sheet.label_width_mm + sheet.gutter_x_mm)
                y = sheet.margin_top_mm + r * (sheet.label_height_mm + sheet.gutter_y_mm)
                page_svg += f"\n  <g transform='translate({x},{y})'>{_embed(svg)}</g>"
                if with_cut_marks:
                    page_svg += _marks(x, y, sheet.label_width_mm, sheet.label_height_mm)
                idx += 1
                items_on_page += 1
        page_svg += "\n</svg>"
        pages.append({"svg": page_svg, "width_mm": sheet.page_width_mm, "height_mm": sheet.page_height_mm})
    return pages


def export_svg_pages(pages, fmt: str = "pdf", dpi: int = 300, pdf_title: str = "labels"):
    if fmt == "pdf":
        # łączymy strony w PDF – cairosvg nie robi multi-page naraz, więc zip lub pojedynczo.
        # MVP: jeżeli >1 strona, zwracamy ZIP pdf-ów.
        if len(pages) == 1:
            buf = cairosvg.svg2pdf(bytestring=pages[0]["svg"].encode("utf-8"))
            return buf, "application/pdf", f"{pdf_title}.pdf"
        else:
            mem = BytesIO()
            with ZipFile(mem, 'w') as z:
                for i, p in enumerate(pages, start=1):
                    pdf_bytes = cairosvg.svg2pdf(bytestring=p["svg"].encode("utf-8"))
                    z.writestr(f"{pdf_title}_{i:02d}.pdf", pdf_bytes)
            return mem.getvalue(), "application/zip", f"{pdf_title}.zip"
    elif fmt == "png":
        if len(pages) == 1:
            png = cairosvg.svg2png(bytestring=pages[0]["svg"].encode("utf-8"), dpi=dpi)
            return png, "image/png", f"{pdf_title}.png"
        else:
            mem = BytesIO()
            with ZipFile(mem, 'w') as z:
                for i, p in enumerate(pages, start=1):
                    png_bytes = cairosvg.svg2png(bytestring=p["svg"].encode("utf-8"), dpi=dpi)
                    z.writestr(f"{pdf_title}_{i:02d}.png", png_bytes)
            return mem.getvalue(), "application/zip", f"{pdf_title}.zip"
    elif fmt == "zip":
        mem = BytesIO()
        with ZipFile(mem, 'w') as z:
            for i, p in enumerate(pages, start=1):
                svg_bytes = p["svg"].encode("utf-8")
                z.writestr(f"{pdf_title}_{i:02d}.svg", svg_bytes)
        return mem.getvalue(), "application/zip", f"{pdf_title}.zip"
    else:
        raise ValueError("unsupported_format")


def _empty_page_svg(sheet: SheetDef) -> str:
    return f"<svg xmlns='http://www.w3.org/2000/svg' width='{sheet.page_width_mm}mm' height='{sheet.page_height_mm}mm' viewBox='0 0 {sheet.page_width_mm} {sheet.page_height_mm}'>\n  <rect x='0' y='0' width='{sheet.page_width_mm}' height='{sheet.page_height_mm}' fill='white'/>"


def _embed(svg: str) -> str:
    # usuń nagłówek svg, zostaw zawartość – prosty sposób
    start = svg.find('>')
    end = svg.rfind('</svg>')
    if start != -1 and end != -1:
        return svg[start+1:end]
    return svg


def _marks(x: float, y: float, w: float, h: float) -> str:
    m = 1.5
    return (
        f"\n  <path d='M {x-m} {y} H {x} M {x} {y-m} V {y}' stroke='#000' stroke-width='0.2'/>"  # TL
        f"\n  <path d='M {x+w} {y} H {x+w+m} M {x+w} {y-m} V {y}' stroke='#000' stroke-width='0.2'/>"  # TR
        f"\n  <path d='M {x-m} {y+h} H {x} M {x} {y+h} V {y+h+m}' stroke='#000' stroke-width='0.2'/>"  # BL
        f"\n  <path d='M {x+w} {y+h} H {x+w+m} M {x+w} {y+h} V {y+h+m}' stroke='#000' stroke-width='0.2'/>"  # BR
    )