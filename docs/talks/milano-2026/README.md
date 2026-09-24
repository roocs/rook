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
| `slides` | Both HTML and PDF. |
| `slides-clean` | Delete generated output for all talks. |

Outputs: `slides.html` and `slides.pdf` in
`docs/_build/talks/milano-2026/`. Generated files are ignored, not committed.
The build copies the canonical `.qmd` and its assets into that directory before
rendering. Edit the source copy in this directory, never the build copy.

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
