"""Prepare the optional Milano PowerPoint export from its canonical Quarto source."""

import argparse
import json
import re
from pathlib import Path

FENCE = re.compile(r"^( {0,3})(`{3,}|~{3,})([^\r\n]*)")


def main_slides(markdown: str) -> str:
    """Stop at the appendix heading, ignoring headings inside code or comments."""
    opened = None
    in_comment = False
    lines = markdown.splitlines(keepends=True)
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
            elif fence[0] == opened[0] and len(fence) >= len(opened) and not info.strip():
                opened = None
        elif opened is None and line.strip() == "# Appendix":
            return re.sub(r"\n---\s*$", "\n", "".join(lines[:index]))
    raise ValueError("Main-slide export requires a '# Appendix' heading")


def template_diagrams(body: str, profile: dict) -> str:
    """Match diagram canvases and edge labels, retaining per-diagram overrides."""
    # Edges cross both the dark canvas and light subgraphs. White disappears
    # inside subgraphs; this mid-tone stays visible on both backgrounds.
    edge_color = "#8794a6"
    label_background = "#f3f4f6"
    label_color = "#111827"
    css = (
        "background: #" + profile["background"] + "; "
        ".flowchart-link { stroke: " + edge_color + " !important; stroke-width: 2.5px !important; } "
        ".marker { fill: " + edge_color + " !important; stroke: " + edge_color + " !important; } "
        ".edgeLabel rect { fill: " + label_background + " !important; opacity: 1 !important; } "
        ".edgeLabel text { fill: " + label_color + " !important; }"
    )

    def configure(match):
        config = json.loads(match.group(1))
        config["themeCSS"] = config.get("themeCSS", "") + " " + css
        variables = config.setdefault("themeVariables", {})
        variables["lineColor"] = edge_color
        variables["edgeLabelBackground"] = label_background
        return "%%{init: " + json.dumps(config) + "}%%"

    return re.sub(r"%%\{init:\s*(\{[^\n]*\})\}%%", configure, body)


def prepare(source: Path, output: Path, template: Path | None = None) -> None:
    """Keep the five main slides and adapt their diagrams for PowerPoint."""
    text = source.read_text(encoding="utf-8")
    metadata, body = text.removeprefix("---\n").split("\n---\n", 1)
    body = main_slides(body)
    body = re.sub(r"^::: \{\.title-(?:copy|photo|date)\}\s*$|^:::\s*$", "", body, flags=re.MULTILINE)
    if template is not None:
        from template_pptx import read_template
        _, _, profile = read_template(template)
        body = template_diagrams(body, profile)
    output.write_text("---\n" + metadata + "\n---\n" + body, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--template", type=Path)
    args = parser.parse_args()
    prepare(args.source, args.output, args.template)
