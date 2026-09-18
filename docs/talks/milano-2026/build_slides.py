"""Generate the Milano Quarto input without changing the canonical Markdown."""

import json
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
fig-responsive: true
keep-md: true
filters:
  - ../../../talks/milano-2026/svg.lua
format:
  revealjs:
    theme:
      - simple
      - ../../../talks/milano-2026/theme.scss
    slide-level: 1
    transition: none
    slide-number: true
    show-slide-number: all
    embed-resources: true
    width: 1600
    height: 900
    margin: 0.06
    center: false
    pdf-max-pages-per-slide: 1
    mermaid-format: svg
    code-overflow: wrap
    auto-stretch: false
---

"""
# One render configuration for all diagrams; no HTML foreignObject labels.
MERMAID_CONFIG = (
    "%%{init: "
    + json.dumps(
        {
            "theme": "base",
            "fontFamily": "Arial",
            "fontSize": 24,
            "htmlLabels": False,
            "flowchart": {
                "htmlLabels": False,
                "subGraphTitleMargin": {"top": 8, "bottom": 28},
            },
            "sequence": {
                "fontSize": 24,
                "actorFontSize": 24,
                "messageFontSize": 24,
                "noteFontSize": 24,
                "mirrorActors": False,
            },
            "themeVariables": {
                "fontFamily": "Arial",
                "fontSize": "24px",
                "primaryColor": "#f3f4f6",
                "primaryTextColor": "#111827",
                "primaryBorderColor": "#6b7280",
                "lineColor": "#6b7280",
                "secondaryColor": "#dceef8",
                "tertiaryColor": "#fff3bf",
                "clusterBkg": "#f3f4f6",
                "clusterBorder": "#6b7280",
                "edgeLabelBackground": "#ffffff",
                "actorBkg": "#f3f4f6",
                "actorBorder": "#6b7280",
                "actorTextColor": "#111827",
                "signalTextColor": "#111827",
                "signalColor": "#6b7280",
            },
        },
        sort_keys=True,
    )
    + "}%%\n"
)
FENCE = re.compile(r"^( {0,3})(`{3,}|~{3,})([^\r\n]*)")


def mermaid_fences(markdown: str, *, convert: bool, configure: bool = False) -> str:
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
                    if configure:
                        line += MERMAID_CONFIG
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


def add_layout(markdown: str) -> str:
    """Annotate slide headings by diagram orientation, without editing content."""
    lines = markdown.splitlines(keepends=True)
    layouts = {}
    heading = None
    opened = None
    in_comment = False
    mermaid = False
    for index, line in enumerate(lines):
        if in_comment:
            in_comment = "-->" not in line
            continue
        if opened is None and "<!--" in line:
            in_comment = "-->" not in line
            continue
        match = FENCE.match(line)
        if match:
            _, fence, info = match.groups()
            if opened is None:
                opened = fence
                # Literal Quarto cell syntax.
                mermaid = info.strip() == "{mermaid}"  # noqa: RUF027
                if mermaid and heading is not None:
                    layouts.setdefault(heading, "diagram-small")
            elif (
                fence[0] == opened[0] and len(fence) >= len(opened) and not info.strip()
            ):
                opened = None
                mermaid = False
        elif opened is None and line.startswith("# "):
            heading = index
        elif (
            mermaid
            and heading is not None
            and line.strip() in {"flowchart TD", "flowchart TB", "sequenceDiagram"}
        ):
            layouts[heading] = "diagram-side"
    for index, layout in layouts.items():
        lines[index] = lines[index].rstrip("\r\n") + " {." + layout + "}\n"
    return "".join(lines)


def transform(markdown: str) -> str:
    """Add Reveal.js metadata, convert Mermaid cells and localize the photo."""
    body = mermaid_fences(markdown, convert=True, configure=True)
    body = add_layout(body)
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
