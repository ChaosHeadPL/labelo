from typing import List, Literal, Optional

from pydantic import (BaseModel, Field, FieldValidationInfo, conint,
                      field_validator)


# ---- I/O for rendering ----
class LabelItem(BaseModel):
    title: str = Field(max_length=200)
    text: Optional[str] = Field(default=None, max_length=500)
    icon: Optional[str] = Field(default=None, description="Pełna nazwa ikony z Tabler Icons, np. 'jar' lub 'truck'.")
    meta: Optional[dict] = None

class RenderOptions(BaseModel):
    sheet: Optional[str] = "A4"
    with_cut_marks: Optional[bool] = False
    preview: Optional[bool] = False
    dpi: Optional[int] = 300
    padding_mm: Optional[float] = 3.0
    bg: Optional[str] = "#ffffff"
    color: Optional[str] = "#111827"
    border: Optional[str] = "#111827"

    def colors_dict(self):
        return {"bg": self.bg, "color": self.color, "border": self.border}

class LabelBatchRequest(BaseModel):
    type: str
    items: List[LabelItem]
    options: RenderOptions = RenderOptions()

class LabelSingleRequest(BaseModel):
    type: str
    item: LabelItem
    options: RenderOptions = RenderOptions()

class TypeDef(BaseModel):
    key: str
    name: str
    width_mm: float
    height_mm: float
    shape: Literal["rect", "round", "oval"]

class TypeListResponse(BaseModel):
    types: List[TypeDef]

class SheetDef(BaseModel):
    key: str
    name: str
    page_width_mm: float
    page_height_mm: float
    cols: int
    rows: int
    label_width_mm: float
    label_height_mm: float
    margin_top_mm: float
    margin_left_mm: float
    gutter_x_mm: float
    gutter_y_mm: float

class SheetListResponse(BaseModel):
    sheets: List[SheetDef]

# ---- Storage ----
class StorageCreate(BaseModel):
    name: str
    description: Optional[str] = None

class StorageOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class StorageLabelCreate(BaseModel):
    template_type: str = Field(default="jar_label_small")
    title: str
    text: Optional[str] = None
    icon: Optional[str] = None
    bg: Optional[str] = None
    color: Optional[str] = None
    border: Optional[str] = None
    desired_qty: conint(ge=0) = 0
    meta: Optional[dict] = None

class StorageLabelOut(BaseModel):
    id: int
    storage_id: int
    template_type: str
    title: str
    text: Optional[str]
    icon: Optional[str]
    bg: Optional[str]
    color: Optional[str]
    border: Optional[str]
    desired_qty: int
    printed_qty: int
    missing_qty: int
    meta: Optional[dict]

    class Config:
        from_attributes = True

class PrintMissingResponse(BaseModel):
    message: Optional[str] = None
    warnings: Optional[list[str]] = None
