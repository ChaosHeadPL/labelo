from app.schemas import SheetDef

SHEETS: dict[str, SheetDef] = {
    # A4 swobodne (user grid w mm)
    "A4": SheetDef(
        key="A4", name="A4 – siatka własna", page_width_mm=210.0, page_height_mm=297.0,
        cols=3, rows=8, label_width_mm=63.5, label_height_mm=36.0,  # domyślne, można nadpisać w przyszłości
        margin_top_mm=10.0, margin_left_mm=10.0, gutter_x_mm=2.0, gutter_y_mm=2.0
    ),
    # Avery przykłady
    "L7160": SheetDef(
        key="L7160", name="Avery L7160 (63.5×38.1, 3×7)", page_width_mm=210.0, page_height_mm=297.0,
        cols=3, rows=7, label_width_mm=63.5, label_height_mm=38.1,
        margin_top_mm=12.0, margin_left_mm=5.0, gutter_x_mm=2.5, gutter_y_mm=0.0
    ),
    "L7163": SheetDef(
        key="L7163", name="Avery L7163 (99.1×38.1, 2×7)", page_width_mm=210.0, page_height_mm=297.0,
        cols=2, rows=7, label_width_mm=99.1, label_height_mm=38.1,
        margin_top_mm=12.7, margin_left_mm=5.0, gutter_x_mm=2.5, gutter_y_mm=0.0
    ),
}

def get_sheet_by_key(key: str) -> SheetDef | None:
    return SHEETS.get(key)