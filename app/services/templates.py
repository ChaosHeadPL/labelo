from app.schemas import TypeDef

# Predefiniowane typy (MVP – łatwo dodać kolejne)
TEMPLATES: dict[str, TypeDef] = {
    "jar_label_small": TypeDef(key="jar_label_small", name="Słoik – mała (58×30)", width_mm=58.0, height_mm=30.0, shape="oval"),
    "jar_label_medium": TypeDef(key="jar_label_medium", name="Słoik – średnia (70×35)", width_mm=70.0, height_mm=35.0, shape="rect"),
    "binder_spine": TypeDef(key="binder_spine", name="Segregator – grzbiet (190×30)", width_mm=190.0, height_mm=30.0, shape="rect"),
    "parcel_medium": TypeDef(key="parcel_medium", name="Przesyłka – 99×67", width_mm=99.0, height_mm=67.0, shape="rect"),
    "round_50": TypeDef(key="round_50", name="Okrągła Ø50", width_mm=50.0, height_mm=50.0, shape="round"),
}

def get_template_by_key(key: str) -> TypeDef | None:
    return TEMPLATES.get(key)
