"""Check the optional PowerPoint export uses the canonical Quarto source."""

import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/talks/milano-2026/slides.qmd"
SPEC = importlib.util.spec_from_file_location(
    "prepare_pptx", SOURCE.with_name("prepare_pptx.py")
)
slides = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(slides)


def test_main_export_uses_qmd_without_modifying_source(tmp_path):
    original = SOURCE.read_bytes()
    output = tmp_path / "slides-main.qmd"
    slides.prepare(SOURCE, output)
    result = output.read_text()
    assert len(re.findall(r"^# ", result, re.MULTILINE)) == 5
    assert "# Appendix" not in result
    assert "# A1." not in result
    assert not result.rstrip().endswith("---")
    assert result.count("```{mermaid}") == 4
    assert "](assets/rook.jpg)" in result
    assert "Photo: Andreas Trepte" in result
    assert "title-photo" not in result
    assert SOURCE.read_bytes() == original


def test_main_export_requires_appendix_boundary():
    with pytest.raises(ValueError, match="requires a '# Appendix' heading"):
        slides.main_slides("# Main slide\n")


def test_main_export_ignores_literal_and_commented_headings():
    main = "# Main\n\n````markdown\n# Appendix\n````\n<!--\n# Appendix\n-->\n"
    assert slides.main_slides(main + "\n---\n\n# Appendix\nExtra") == main + "\n"


def test_template_diagrams_preserve_local_overrides():
    body = slides.main_slides(SOURCE.read_text())
    result = slides.template_diagrams(body, {"background": "222A35", "foreground": "FFFFFF"})
    configs = [slides.json.loads(value) for value in re.findall(r"%%\{init:\s*(\{[^\n]*\})\}%%", result)]
    assert len(configs) == 6
    for config in configs:
        assert "background: #222A35" in config["themeCSS"]
        assert config["themeVariables"]["lineColor"] == "#8794a6"
        assert config["themeVariables"]["edgeLabelBackground"] == "#f3f4f6"
        assert ".edgeLabel text { fill: #111827" in config["themeCSS"]
        assert ".marker { fill: #8794a6" in config["themeCSS"]
    assert any(".cluster-label { font-size: 20px; }" in config["themeCSS"] for config in configs)
    assert any(config.get("flowchart", {}).get("subGraphTitleMargin", {}).get("bottom") == 64 for config in configs)
