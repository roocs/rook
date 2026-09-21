# Milano 2026 slides

Edit only [`Rook_WPS_ESGF2_talk_draft.md`](../../../Rook_WPS_ESGF2_talk_draft.md).
Complete the [environment setup](../README.md), then run from `docs/talks/`:

```bash
conda activate rook
make slides
```

| Target (`make <target>`) | Output |
| --- | --- |
| `slides-html` | Reveal.js HTML via Quarto. |
| `slides-pdf` | HTML, then PDF via DeckTape. |
| `slides-pptx` | Five main slides as PowerPoint, without the appendix. |
| `slides` | Both HTML and PDF. |
| `slides-clean` | Delete only this talk's generated output. |

Outputs: `slides.qmd`, `slides.html`, `slides.pdf`, and `slides.pptx` in
`docs/_build/talks/milano-2026/`. These generated files are ignored, not committed.

`build_slides.py` adds Quarto metadata, converts ` ```mermaid ` to
` ```{mermaid} `, and uses the [local rook photo](assets/README.md).
It preserves the source, diagram definitions, image link, attribution and
hidden presenter comments. The generated `.qmd` is not a second content source.

Run `make slides-pptx` for PowerPoint. It generates `slides-main.qmd` from
everything before `# Appendix`, renders `slides-raw.pptx` with Quarto, then
`style_pptx.py` combines continuation slides and lays out the five main slides.
Text and links remain editable; diagrams are embedded PNGs and the rook photo
is included with its attribution. This uses the same Quarto and Chrome setup
as HTML and does not require DeckTape's PDF export step. HTML and PDF retain
the appendix. The layout checks fail if the main slide structure changes,
so update `style_pptx.py` when adding slides or changing their content blocks.

Diagrams are prerendered SVG with plain SVG text. `svg.lua` embeds them as
images, avoiding Quarto/Pandoc sequence-CSS parsing and PDF font scaling bugs.
The ignored `slides.revealjs.md` is its intermediate input. No Mermaid runtime
is needed to draw the final slides.

Layout is inferred from Mermaid orientation: TD/TB and sequence diagrams use
`.diagram-side`; wide diagrams use `.diagram-small`. These classes and shared
font settings are added only during conversion. Source `classDef` colors use
blue for existing Rook components, amber for proposed components and grey for
supporting infrastructure. Label words and connections stay unchanged; HTML line breaks are replaced by plain separators.

## Preview

```bash
python milano-2026/build_slides.py
sh ./quarto.sh preview ../_build/talks/milano-2026/slides.qmd
```

Rerun the script after editing the source. Press **S** in the preview for
speaker view. Check slide fit, diagrams and links before presenting.

## Tests

```bash
pytest --confcutdir=../../tests/slides -o addopts='' ../../tests/slides
```

Tests need neither Quarto nor DeckTape.
