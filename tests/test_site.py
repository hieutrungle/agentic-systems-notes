"""Check page coverage and local links in the generated Pages artifact."""

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
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if anchor := attributes.get("id"):
            self.anchors.add(anchor)
        attribute = {"a": "href", "img": "src", "video": "src", "source": "src"}.get(tag)
        if attribute and (value := attributes.get(attribute)):
            self.local_links.append(value)


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

    return errors


if __name__ == "__main__":
    site = Path(sys.argv[1]).resolve()
    source = Path(__file__).resolve().parents[1] / "docs"
    errors = check_site(site, source)
    if errors:
        sys.exit("\n".join(errors))
    print("Verified rendered pages, local links, and bibliography entries.")
