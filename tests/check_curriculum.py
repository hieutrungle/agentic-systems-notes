"""Validate the canonical curriculum, rendered navigation, and optional blog mirror."""

import argparse
import json
import posixpath
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


SOURCE = Path(__file__).resolve().parents[1] / "docs" / "curriculum"
NUMBERS = [f"{number:02d}" for number in range(1, 15)]
SLUG = r"[0-9]{2}-[a-z]+(?:-[a-z]+)*"
QUOTED = r'"(?:[^"\\]|\\.)*"'
INDEX_ROW = re.compile(rf"^\| ([0-9]{{2}}) \| \[([^\]]+)\]\(({SLUG})\.qmd\) \| .+ \|$", re.M)
BLOG_ENTRY = re.compile(rf"- title: ({QUOTED})\n +page: ({SLUG}\.html)\n")


@dataclass(frozen=True)
class Block:
    slug: str
    title: str
    aliases: tuple[str, ...]

    @property
    def page(self) -> str:
        return f"{self.slug}.html"


def canonical_blocks() -> list[Block]:
    rows = INDEX_ROW.findall((SOURCE / "index.qmd").read_text(encoding="utf-8"))
    if [number for number, _, _ in rows] != NUMBERS:
        raise ValueError("Curriculum index must list blocks 01–14 once each and in order.")
    files = {path.stem for path in SOURCE.glob("[0-9]*.qmd")}
    if files != {slug for _, _, slug in rows}:
        raise ValueError("Numbered curriculum source files must match the index.")

    blocks = []
    for number, title, slug in rows:
        if slug[:2] != number:
            raise ValueError(f"Block {number} links to a differently numbered file: {slug}")
        source = (SOURCE / f"{slug}.qmd").read_text(encoding="utf-8")
        header = re.match(r"^---\n(.*?)\n---\n", source, re.S)
        if not header:
            raise ValueError(f"Missing front matter in {slug}.qmd")
        title_line = re.search(rf"^title: ({QUOTED})$", header[1], re.M)
        if not title_line or json.loads(title_line[1]) != title:
            raise ValueError(f"Title of {slug}.qmd does not match block {number} in the index.")
        aliases = re.findall(rf"^  - ({SLUG}\.html)$", header[1], re.M)
        blocks.append(Block(slug, title, tuple(aliases)))

    legacy = [alias for block in blocks for alias in block.aliases]
    if sorted(alias[:2] for alias in legacy) != NUMBERS:
        raise ValueError("Expected one legacy redirect for each original block number 01–14.")
    if set(legacy) & {block.page for block in blocks}:
        raise ValueError("A legacy redirect must have a path distinct from every canonical page.")
    return blocks


def check_blog(path: Path, blocks: list[Block]) -> None:
    # The mirror uses two fields per entry, with a JSON-compatible quoted YAML title.
    lines = path.read_text(encoding="utf-8").splitlines()
    entries = "".join(
        f"{line.rstrip()}\n"
        for line in lines
        if line.strip() and not line.lstrip().startswith("#")
    )
    if BLOG_ENTRY.sub("", entries):
        raise ValueError(f"Expected quoted title and relative HTML page fields in {path}.")
    visible = [(json.loads(title), page) for title, page in BLOG_ENTRY.findall(entries)]
    if len(visible) != len(blocks):
        raise ValueError(f"Blog roadmap has {len(visible)} entries, expected {len(blocks)}.")
    for block, (title, page) in zip(blocks, visible):
        if (title, page) != (block.title, block.page):
            raise ValueError(
                f"Blog roadmap block {block.slug[:2]} is {title!r} at {page}. "
                f"Expected {block.title!r} at {block.page}."
            )


class RenderedPage(HTMLParser):
    def __init__(self, html: str):
        super().__init__()
        self.heading: list[str] = []
        self.sidebar: list[str] = []
        self.pagination: list[str] = []
        self.in_heading = False
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "h1":
            self.in_heading = True
        if tag == "a":
            attributes = dict(attrs)
            classes = attributes.get("class", "").split()
            href = attributes.get("href", "")
            if "sidebar-link" in classes:
                self.sidebar.append(posixpath.normpath(posixpath.join("curriculum", href)))
            if "pagination-link" in classes:
                self.pagination.append(posixpath.normpath(posixpath.join("curriculum", href)))

    def handle_endtag(self, tag):
        if tag == "h1":
            self.in_heading = False

    def handle_data(self, data):
        if self.in_heading:
            self.heading.append(data)


def check_title(html: str, block: Block) -> RenderedPage:
    rendered = RenderedPage(html)
    if "".join(rendered.heading).strip() != block.title:
        raise ValueError(f"Rendered heading for {block.page} must be {block.title!r}.")
    return rendered


def check_local_site(site: Path, blocks: list[Block]) -> None:
    pages = ["curriculum/index.html", *(f"curriculum/{block.page}" for block in blocks)]
    index = RenderedPage((site / pages[0]).read_text(encoding="utf-8"))
    if index.sidebar != pages or index.pagination != pages[1:2]:
        raise ValueError("Curriculum index navigation does not match the canonical sequence.")

    for number, block in enumerate(blocks, start=1):
        rendered = check_title((site / pages[number]).read_text(encoding="utf-8"), block)
        expected = pages[number - 1:number] + pages[number + 1:number + 2]
        if rendered.sidebar != pages or rendered.pagination != expected:
            raise ValueError(f"Sidebar or previous/next navigation drift in {block.page}.")
        for alias in block.aliases:
            redirect = (site / "curriculum" / alias).read_text(encoding="utf-8")
            # Quarto 1.11 emits the alias targets as a JSON map in its redirect template.
            targets = re.search(r"var redirects = (\{[^\n]*\});", redirect)
            if not targets or json.loads(targets[1]) != {"": block.page}:
                raise ValueError(f"Expected {alias} to redirect directly to {block.page}.")


def check_live_page(site_url: str, block: Block) -> None:
    url = f"{site_url.rstrip('/')}/curriculum/{block.page}"
    request = Request(url, headers={"Cache-Control": "no-cache"})
    with urlopen(request, timeout=20) as response:
        if response.geturl() != url:
            raise ValueError(f"Canonical URL {url} unexpectedly redirected to {response.geturl()}.")
        check_title(response.read().decode("utf-8"), block)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    location = parser.add_mutually_exclusive_group(required=True)
    location.add_argument("--site", type=Path, help="Path to a local Quarto render")
    location.add_argument("--live-site", help="Published Quarto site URL")
    parser.add_argument("--blog-roadmap", type=Path, help="Blog Agentic Systems YAML mirror")
    args = parser.parse_args()
    try:
        blocks = canonical_blocks()
        if args.blog_roadmap:
            check_blog(args.blog_roadmap, blocks)
        if args.site:
            check_local_site(args.site, blocks)
        else:
            with ThreadPoolExecutor(max_workers=4) as pool:
                list(pool.map(lambda block: check_live_page(args.live_site, block), blocks))
    except (OSError, ValueError) as error:
        sys.exit(str(error))

    checks = "canonical pages and numbering"
    if args.site:
        checks += ", sidebar, pagination, and legacy redirects"
    if args.blog_roadmap:
        checks += ", and blog roadmap parity"
    print(f"Verified {len(blocks)} blocks: {checks}.")


if __name__ == "__main__":
    main()
