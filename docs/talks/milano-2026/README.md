# Milano 2026 slides

Edit [`slides.qmd`](slides.qmd), the only source for this deck.
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
| `slides-clean` | Delete generated output for all talks. |

Outputs: `slides.html`, `slides.pdf`, and optional `slides.pptx` in
`docs/_build/talks/milano-2026/`. Generated files are ignored, not committed.
The build copies the canonical `.qmd` and its assets into that directory before
rendering. Edit the source copy in this directory, never the build copy.

Run `make slides-pptx` for PowerPoint. `prepare_pptx.py` extracts everything
before `# Appendix` from the same `.qmd`. Quarto renders `slides-raw.pptx`,
then `style_pptx.py` lays out the five main slides.
Text and links remain editable; diagrams are embedded PNGs and the rook photo
is included with its attribution. This uses the same Quarto and Chrome setup
as HTML and does not require DeckTape's PDF export step. HTML and PDF retain
the appendix. The layout checks fail if the main slide structure changes,
so update `style_pptx.py` when adding slides or changing their content blocks.

### Futura black PowerPoint template

`slides-pptx` automatically uses `../templates/futura_black.potx` when present.
The local copy comes from Woodpecker. The template directory is ignored by Git
and survives `slides-clean`; generated PPTX files contain the template artwork.
`template_pptx.py` reuses the reference's master, layout, logo, footer and fonts,
adapts the five content layouts, and matches diagram backgrounds to its dark
palette. Text remains editable, with explicit text-box geometry for Google Slides.
The template fonts must be installed for exact typography.

```bash
make slides-pptx                       # Futura black when installed locally
make slides-pptx PPTX_TEMPLATE=         # original light styling
make slides-pptx PPTX_TEMPLATE=/path/to/reference.potx
```

References must contain one selected slide on a 13⅓ by 7½ inch canvas.
Template styling applies only to PPTX; HTML and PDF use the Reveal.js theme.

Diagrams are prerendered SVG with plain SVG text. `svg.lua` embeds them as
images, avoiding Quarto/Pandoc sequence-CSS parsing and PDF font scaling bugs.
The ignored `slides.revealjs.md` is its intermediate input. No Mermaid runtime
is needed to draw the final slides.

Layout is explicit in the `.qmd`: TD/TB and sequence diagrams use
`.diagram-side`; wide diagrams use `.diagram-small`. These classes and per-diagram
Mermaid settings are edited directly in the source. Source `classDef` colors use
blue for existing Rook components, amber for proposed components and grey for
supporting infrastructure.

## Preview

```bash
make prepare
sh ./quarto.sh preview ../_build/talks/milano-2026/slides.qmd
```

Rerun `make prepare` after editing the source. Press **S** in the preview for
speaker view. Check slide fit, diagrams and links before presenting.

## Tests

```bash
pytest --confcutdir=../../tests/slides -o addopts='' ../../tests/slides
```

Tests need neither Quarto nor DeckTape.
