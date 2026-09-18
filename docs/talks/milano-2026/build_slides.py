"""Generate the Milano Quarto input without changing the canonical Markdown."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "Rook_WPS_ESGF2_talk_draft.md"
ASSET = ROOT / "docs/talks/milano-2026/assets/rook.jpg"
OUTPUT = ROOT / "docs/_build/talks/milano-2026/slides.qmd"
LOCAL_IMAGE = "../../../talks/milano-2026/assets/rook.jpg"
REMOTE_IMAGES = (
    "https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b5/"
    "Rook-Corvus_frugilegus.jpg/960px-Rook-Corvus_frugilegus.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/b/b5/Rook-Corvus_frugilegus.jpg",
)
FRONT_MATTER = """---
pagetitle: "Rook/WPS for ESGF2 — Milano 2026"
format:
  revealjs:
    theme:
      - simple
      - ../../../talks/milano-2026/theme.scss
    slide-level: 1
    transition: none
    slide-number: true
    show-slide-number: print
    embed-resources: true
    width: 1600
    height: 900
    margin: 0.06
    center: false
    pdf-max-pages-per-slide: 1
    mermaid-format: js
    code-overflow: wrap
    auto-stretch: false
---

"""
FENCE = re.compile(r"^( {0,3})(`{3,}|~{3,})([^\r\n]*)")


def mermaid_fences(markdown: str, *, convert: bool) -> str:
    """Convert only opening Mermaid fences and reject unclosed code blocks."""
    opened = None
    lines = []
    for number, line in enumerate(markdown.splitlines(keepends=True), 1):
        match = FENCE.match(line)
        if match:
            indent, fence, info = match.groups()
            if opened is None:
                opened = (fence, number)
                if info.strip() == "mermaid":
                    if not convert:
                        raise ValueError(
                            f"Plain Mermaid opening fence remains at line {number}"
                        )
                    line = (
                        indent
                        + fence
                        + info.replace("mermaid", "{mermaid}")
                        + line[match.end() :]
                    )
            elif (
                fence[0] == opened[0][0]
                and len(fence) >= len(opened[0])
                and not info.strip()
            ):
                opened = None
        lines.append(line)
    if opened is not None:
        raise ValueError(f"Unbalanced fenced code block opened at line {opened[1]}")
    return "".join(lines)


def transform(markdown: str) -> str:
    """Add Reveal.js metadata, convert Mermaid cells and localize the photo."""
    body = mermaid_fences(markdown, convert=True)
    for remote in REMOTE_IMAGES:
        body = body.replace(f"]({remote})", f"]({LOCAL_IMAGE})")
    result = FRONT_MATTER + body
    mermaid_fences(result, convert=False)
    if f"]({LOCAL_IMAGE})" not in result:
        raise ValueError(
            "Required local rook image path is missing; check the source image URL"
        )
    return result


def build(source: Path = SOURCE, asset: Path = ASSET, output: Path = OUTPUT) -> Path:
    """Write deterministic Quarto input after checking the required source files."""
    for path, description in (
        (source, "Canonical Markdown source"),
        (asset, "Required local rook image"),
    ):
        if not path.is_file():
            raise FileNotFoundError(f"{description} is missing: {path}")
    result = transform(source.read_text(encoding="utf-8"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result, encoding="utf-8")
    return output


def main() -> int:
    """Report actionable build errors without a Python traceback."""
    try:
        output = build()
    except (OSError, ValueError) as error:
        print(f"Slides: {error}", file=sys.stderr)
        return 1
    print(f"Generated {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
