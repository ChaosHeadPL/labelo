from typing import Optional, Tuple

from app.schemas import LabelItem
from app.services.icons import IconResolver
from app.services.templates import TypeDef

SVG_NS = "http://www.w3.org/2000/svg"

# Prosty layout tekstu – przyjmujemy stałe fonty
FONT_FAMILY = "Inter, 'Noto Color Emoji', sans-serif"


def escape(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_label_svg(
    item: LabelItem,
    template: TypeDef,
    icon_resolver: IconResolver,
    colors: dict,
    padding_mm: float = 3.0,
    outline_icons: bool = True,
) -> Tuple[str, float, float, list[str]]:
    w = template.width_mm
    h = template.height_mm
    warnings: list[str] = []

    # ikona
    icon_svg, iwarn = icon_resolver.load_icon_svg(item.icon)
    warnings.extend(iwarn)

    # proste marginesy
    inner_w = w - 2 * padding_mm
    inner_h = h - 2 * padding_mm

    # style CSS
    css = f"""
    .root {{ background: {colors.get('bg', '#fff')}; }}
    .border {{ stroke: {colors.get('border', '#111')}; fill: none; }}
    .title {{ font-family: {FONT_FAMILY}; font-size: {min(inner_h*0.35, 10):.1f}mm; font-weight: 700; fill: {colors.get('color','#111')}; }}
    .text {{ font-family: {FONT_FAMILY}; font-size: {min(inner_h*0.22, 6):.1f}mm; font-weight: 400; fill: {colors.get('color','#111')}; }}
    .icon {{ width: {min(inner_h, inner_w)*0.8:.2f}mm; height: {min(inner_h, inner_w)*0.8:.2f}mm; color: {colors.get('color','#111')}; }}
    """

    # kształt obrysu
    if template.shape == "round":
        border = f'<circle class="border" cx="{w/2}" cy="{h/2}" r="{min(w,h)/2 - 0.4}" stroke-width="0.4" />'
    elif template.shape == "oval":
        border = f'<rect class="border" x="0.2" y="0.2" rx="{h/2 - 0.2}" ry="{h/2 - 0.2}" width="{w-0.4}" height="{h-0.4}" stroke-width="0.4" />'
    else:
        border = f'<rect class="border" x="0.2" y="0.2" rx="1.2" ry="1.2" width="{w-0.4}" height="{h-0.4}" stroke-width="0.4" />'

    # pozycje – ikona po lewej, tekst po prawej (lub centralnie jeśli brak ikony)
    icon_block = ""
    text_x = padding_mm
    if icon_svg:
        icon_size = min(inner_h, inner_w) * 0.8
        icon_x = padding_mm
        icon_y = (h - icon_size) / 2
        # osadź jako foreignObject lub inline group – tu inline raw SVG w <g>
        icon_block = f'<g transform="translate({icon_x},{icon_y}) scale({icon_size/24})" class="icon">{icon_svg}</g>'
        text_x = padding_mm + icon_size + (padding_mm * 0.5)

    # Tekst – tytuł i opis
    title = escape(item.title)
    text = escape(item.text or "")
    title_y = padding_mm + (inner_h * 0.45)
    text_y = title_y + min(inner_h*0.28, 7)

    content = f"""
    <svg xmlns='{SVG_NS}' width='{w}mm' height='{h}mm' viewBox='0 0 {w} {h}'>
      <style>{css}</style>
      <rect class='root' x='0' y='0' width='{w}' height='{h}' fill='{colors.get('bg','#fff')}'/>
      {border}
      {icon_block}
      <text class='title' x='{text_x:.2f}' y='{title_y:.2f}'>{title}</text>
      <text class='text' x='{text_x:.2f}' y='{text_y:.2f}'>{text}</text>
    </svg>
    """.strip()
    return content, w, h, warnings