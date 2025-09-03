from pathlib import Path
from typing import Optional


class IconResolver:
    def __init__(self, base_dir: str):
        self.base = Path(base_dir)

    def load_icon_svg(self, name: Optional[str]) -> tuple[Optional[str], list[str]]:
        warnings = []
        if not name:
            return None, warnings
        # pełna nazwa z biblioteki – akceptujemy np. "jar" albo "icon-jar"
        fname = name
        if not fname.endswith(".svg"):
            fname = f"{fname}.svg"
        # strip ewentualnego prefixu
        fname = fname.replace("icon-", "")
        path = self.base / fname
        if not path.exists():
            warnings.append(f"icon_missing:{name}")
            return None, warnings
        try:
            svg = path.read_text(encoding="utf-8")
            # usuwamy fill aby móc sterować kolorem przez CSS
            svg = svg.replace('fill="none"', '').replace('stroke="currentColor"', 'stroke="currentColor"')
            return svg, warnings
        except Exception as e:
            warnings.append(f"icon_load_error:{name}")
            return None, warnings
