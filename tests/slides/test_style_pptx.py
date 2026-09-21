"""Regression checks for editable text in PowerPoint importers."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("style_pptx", ROOT / "docs/talks/milano-2026/style_pptx.py")
style = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(style)


@pytest.mark.parametrize("placeholder", ['type="title"', 'idx="1"', 'idx="2" type="body"'])
def test_detached_placeholder_becomes_explicit_editable_text_box(placeholder):
    shape = style.ET.fromstring(
        f'<p:sp xmlns:p="{style.NS["p"]}" xmlns:a="{style.NS["a"]}" xmlns:r="{style.NS["r"]}">'
        '<p:nvSpPr><p:cNvPr id="2" name="Text"/><p:cNvSpPr/>'
        f"<p:nvPr><p:ph {placeholder}/></p:nvPr></p:nvSpPr><p:spPr/>"
        "<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:buNone/></a:pPr>"
        '<a:r><a:rPr b="1"><a:hlinkClick r:id="rId4"/></a:rPr><a:t>Editable link</a:t></a:r>'
        "</a:p></p:txBody></p:sp>"
    )
    style.place(shape, (0.65, 1.4, 12.05, 1.8))
    bounds = style.ET.tostring(shape.find("p:spPr/a:xfrm", style.NS))
    style.style_text(shape)
    assert shape.find(".//p:ph", style.NS) is None
    assert shape.find("p:nvSpPr/p:cNvSpPr", style.NS).get("txBox") == "1"
    props = shape.find("p:spPr", style.NS)
    assert [node.tag for node in props] == [style.tag(name) for name in ("a:xfrm", "a:prstGeom", "a:noFill", "a:ln")]
    assert props.find("a:prstGeom", style.NS).get("prst") == "rect"
    assert props.find("a:prstGeom/a:avLst", style.NS) is not None
    assert props.find("a:ln/a:noFill", style.NS) is not None
    assert style.ET.tostring(props.find("a:xfrm", style.NS)) == bounds
    assert style.text(shape) == "Editable link"
    assert shape.find(".//a:hlinkClick", style.NS).get(style.tag("r:id")) == "rId4"
    assert shape.find(".//a:rPr", style.NS).get("b") == "1"
    first = style.ET.tostring(shape)
    style.style_text(shape)
    assert style.ET.tostring(shape) == first
