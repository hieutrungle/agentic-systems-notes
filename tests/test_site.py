"""Check pages, local links, bibliography, and dark-theme contrast."""

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Page(HTMLParser):
    def __init__(self, path: Path):
        super().__init__()
        self.local_links: list[str] = []
        self.anchors: set[str] = set()
        self.dark_stylesheet: str | None = None
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if anchor := attributes.get("id"):
            self.anchors.add(anchor)
        attribute = {"a": "href", "img": "src", "video": "src", "source": "src"}.get(tag)
        if attribute and (value := attributes.get(attribute)):
            self.local_links.append(value)
        if (
            tag == "link"
            and attributes.get("id") == "quarto-bootstrap"
            and attributes.get("data-mode") == "dark"
            and "quarto-color-alternate" in attributes.get("class", "").split()
        ):
            self.dark_stylesheet = attributes.get("href")


def css_value(css: str, selector: str, property_name: str) -> str:
    """Read a declaration from a known rule in Quarto's compiled CSS."""
    rules = re.findall(rf"(?:^|[{{}}]|,\s*){re.escape(selector)}\s*\{{([^{{}}]*)\}}", css)
    for rule in reversed(rules):
        value = re.search(rf"(?:^|;)\s*{re.escape(property_name)}:\s*([^;]+)", rule)
        if value:
            return value[1].strip()
    return ""


def luminance(hex_color: str) -> float:
    digits = hex_color[1:]
    if len(digits) == 3:
        digits = "".join(digit * 2 for digit in digits)
    channels = [int(digits[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
    return sum(v * weight for v, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


def check_dark_theme(site: Path, lesson: Path, page: Page) -> list[str]:
    if not page.dark_stylesheet:
        return ["Block 01 must load an alternate dark Bootstrap stylesheet."]
    stylesheet = (lesson.parent / page.dark_stylesheet).resolve()
    if not stylesheet.is_relative_to(site) or not stylesheet.is_file():
        return [f"Missing dark Bootstrap stylesheet {page.dark_stylesheet}"]

    css = stylesheet.read_text(encoding="utf-8")
    body = re.search(r"--bs-body-bg:\s*(#[0-9a-fA-F]+)[;} ]", css)
    body_bg = body[1] if body else ""
    code_bg = css_value(css, "main.content pre:not(.sourceCode,.mermaid-js)", "background-color")
    colors = (
        ("plain fenced code", css_value(css, "pre", "color"), code_bg),
        ("sidebar links", css_value(css, "div.sidebar-item-container", "color"), body_bg),
        ("table of contents", css_value(css, "#TOC", "color"), body_bg),
    )
    errors = []
    if css_value(css, "pre code", "color") != "inherit":
        errors.append("Code inside pre must inherit the explicit pre foreground.")
    for label, foreground, background in colors:
        if any(not re.fullmatch(r"#(?:[0-9a-f]{3}){1,2}", color, re.I) for color in (foreground, background)):
            errors.append(f"Missing explicit dark-mode colors for {label}.")
            continue
        low, high = sorted((luminance(foreground), luminance(background)))
        contrast = (high + 0.05) / (low + 0.05)
        if contrast < 4.5:
            errors.append(f"Dark-mode contrast for {label} is {contrast:.2f}:1, below 4.5:1.")
    return errors


def check_site(site: Path, source: Path) -> list[str]:
    errors = []
    for document in source.rglob("*.qmd"):
        if not (site / document.relative_to(source).with_suffix(".html")).is_file():
            errors.append(f"Missing rendered page for {document.relative_to(source)}")

    blocks = sorted(path.name[:2] for path in (source / "curriculum").glob("[0-9]*.qmd"))
    if blocks != [f"{number:02d}" for number in range(1, 15)]:
        errors.append("Expected one curriculum page for each block from 01 to 14")

    pages = {
        path: Page(path)
        for path in site.rglob("*.html")
        if not any(
            part.endswith("_files") or part == "site_libs"
            for part in path.relative_to(site).parts
        )
    }

    for path, page in pages.items():
        for link in page.local_links:
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                continue

            relative = unquote(parsed.path)
            if relative.startswith("/"):
                errors.append(f"{path.relative_to(site)}: root-relative link {link}")
                continue

            target = (path.parent / relative).resolve() if relative else path
            if target.is_dir():
                target = target / "index.html"
            if not target.is_relative_to(site) or not target.is_file():
                errors.append(f"{path.relative_to(site)}: broken local link {link}")
            elif parsed.fragment and target in pages:
                if unquote(parsed.fragment) not in pages[target].anchors:
                    errors.append(f"{path.relative_to(site)}: missing anchor {link}")

    bibliography = (source / "references.bib").read_text(encoding="utf-8")
    keys = set(re.findall(r"^@\w+\{([^,]+),", bibliography, flags=re.MULTILINE))
    rendered_references = site / "literature/references.html"
    if rendered_references.is_file():
        index = rendered_references.read_text(encoding="utf-8")
        for key in sorted(keys):
            if f'id="ref-{key}"' not in index:
                errors.append(f"Missing rendered bibliography entry {key}")

    lesson = site / "curriculum/01-agent-fundamentals.html"
    if lesson in pages:
        errors.extend(check_dark_theme(site, lesson, pages[lesson]))

    return errors


if __name__ == "__main__":
    site = Path(sys.argv[1]).resolve()
    source = Path(__file__).resolve().parents[1] / "docs"
    errors = check_site(site, source)
    if errors:
        sys.exit("\n".join(errors))
    print("Verified rendered pages, local links, bibliography entries, and dark-theme contrast.")
