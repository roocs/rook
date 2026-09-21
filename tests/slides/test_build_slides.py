"""Standalone presentation tests; no climate data or rendering tools needed."""

import importlib.util
import re
import subprocess  # noqa: S404 -- read-only Git ignore check
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "build_slides", ROOT / "docs/talks/milano-2026/build_slides.py"
)
slides = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(slides)


@pytest.fixture
def presentation(tmp_path):
    source = tmp_path / "Rook_WPS_ESGF2_talk_draft.md"
    source.write_bytes(slides.SOURCE.read_bytes())
    asset = tmp_path / "docs/talks/milano-2026/assets/rook.jpg"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(slides.ASSET.read_bytes())
    output = tmp_path / "docs/_build/talks/milano-2026/slides.qmd"
    return source, asset, output


def test_build_preserves_content_and_paths(presentation):
    source, asset, output = presentation
    original = source.read_bytes()
    slides.build(source, asset, output)
    result = output.read_text(encoding="utf-8")
    assert result.startswith(slides.FRONT_MATTER)
    assert "slide-level: 1" in result
    assert "mermaid-format: svg" in result
    assert "fig-responsive: true" in result
    assert "keep-md: true" in result
    assert "../../../talks/milano-2026/svg.lua" in result
    assert "```mermaid" not in result
    assert result.count("```{mermaid}") == original.count(b"```mermaid")
    assert (output.parent / slides.LOCAL_IMAGE).resolve() == asset
    assert slides.LOCAL_IMAGE in result
    assert (
        "https://commons.wikimedia.org/wiki/File:Rook-Corvus_frugilegus.jpg" in result
    )
    assert "Photo: Andreas Trepte" in result
    assert "https://creativecommons.org/licenses/by-sa/2.5/" in result
    # Exact round trip checks Python blocks, diagrams, slide breaks and comments.
    restored = result.removeprefix(slides.FRONT_MATTER).replace(
        "```{mermaid}", "```mermaid"
    )
    restored = restored.replace(slides.LOCAL_IMAGE, slides.REMOTE_IMAGES[0])
    restored = restored.replace(slides.MERMAID_CONFIG, "")
    restored = re.sub(r" \{\.diagram-(?:side|small)\}(?=\n)", "", restored)
    assert restored.encode("utf-8") == original
    assert source.read_bytes() == original
    assert slides.mermaid_fences(result, convert=False) == result
    first = output.read_bytes()
    slides.build(source, asset, output)
    assert output.read_bytes() == first


@pytest.mark.parametrize(
    "missing, message",
    [(0, "Canonical Markdown source"), (1, "Required local rook image")],
)
def test_missing_input(presentation, missing, message):
    presentation[missing].unlink()
    with pytest.raises(FileNotFoundError, match=message):
        slides.build(*presentation)
    assert not presentation[2].exists()


@pytest.mark.parametrize("fence", ["```", "````", "~~~"])
def test_opening_fences(fence):
    body = f"{fence}mermaid\nflowchart LR\n A --> B\n{fence}\n"
    assert slides.mermaid_fences(body, convert=True) == body.replace(
        "mermaid", "{mermaid}"
    )


def test_literal_fences_inside_code_are_unchanged():
    body = "````markdown\n```mermaid\nA --> B\n```\n````\n```python\nprint('hi')\n```\n"
    assert slides.mermaid_fences(body, convert=True) == body


@pytest.mark.parametrize(
    "body", ["```python\nprint(1)\n", "```mermaid\nA --> B\n~~~\n"]
)
def test_unbalanced_fences(body):
    with pytest.raises(ValueError, match="Unbalanced fenced code block"):
        slides.mermaid_fences(body, convert=True)


def test_validation_rejects_plain_mermaid():
    with pytest.raises(ValueError, match="Plain Mermaid opening fence"):
        slides.mermaid_fences("```mermaid\nA --> B\n```\n", convert=False)


def test_validation_requires_image():
    with pytest.raises(ValueError, match="local rook image path is missing"):
        slides.transform("# Missing image\n")


def test_cli_error(presentation, monkeypatch, capsys):
    source, asset, output = presentation
    source.unlink()
    build = slides.build
    monkeypatch.setattr(slides, "build", lambda: build(source, asset, output))
    assert slides.main([]) == 1
    assert "Canonical Markdown source is missing" in capsys.readouterr().err


def test_layout_is_based_on_diagram_not_slide_number():
    body = "# Arbitrary title\n\n```{mermaid}\nflowchart TD\nA --> B\n```\n"
    assert "# Arbitrary title {.diagram-side}" in slides.add_layout(body)
    assert "# Arbitrary title {.diagram-small}" in slides.add_layout(
        body.replace("TD", "LR")
    )


def test_layout_ignores_code_examples_and_comments():
    body = "# A slide\n\n````markdown\n# Example\n```{mermaid}\nflowchart TD\n```\n````\n<!--\n# Hidden\n-->\n"
    assert slides.add_layout(body) == body
    assert slides.mermaid_fences(body, convert=True, configure=True) == body


def test_shared_config_disables_html_labels():
    config = slides.json.loads(
        slides.MERMAID_CONFIG.removeprefix("%%{init: ").removesuffix("}%%\n")
    )
    assert config["htmlLabels"] is False
    assert config["flowchart"]["htmlLabels"] is False
    assert config["themeVariables"]["fontFamily"].startswith("Arial")


def test_generated_outputs_are_ignored():
    paths = [
        f"docs/_build/talks/milano-2026/slides.{suffix}"
        for suffix in ("qmd", "html", "pdf", "pptx", "revealjs.md")
    ]
    result = subprocess.run(  # noqa: S603, S607 -- read-only Git ignore check with fixed arguments
        ["git", "check-ignore", "--stdin"],  # noqa: S607 -- fixed Git command
        input="\n".join(paths),
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.splitlines() == paths


def test_main_export_excludes_appendix(presentation):
    source, asset, output = presentation
    original = source.read_bytes()
    slides.build(source, asset, output, main_only=True)
    result = output.read_text()
    assert len(re.findall(r"^# ", result, re.MULTILINE)) == 5
    assert "# Appendix" not in result
    assert "# A1." not in result
    assert not result.rstrip().endswith("---")
    assert result.count("```{mermaid}") == 4
    assert slides.LOCAL_IMAGE in result
    assert "Photo: Andreas Trepte" in result
    assert "title-photo" not in result
    assert source.read_bytes() == original


def test_main_export_requires_appendix_boundary():
    with pytest.raises(ValueError, match="requires a '# Appendix' heading"):
        slides.main_slides("# Main slide\n")


def test_main_export_ignores_literal_and_commented_headings():
    main = "# Main\n\n````markdown\n# Appendix\n````\n<!--\n# Appendix\n-->\n"
    assert slides.main_slides(main + "\n---\n\n# Appendix\nExtra") == main + "\n"
