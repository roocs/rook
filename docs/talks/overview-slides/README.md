# Rook overview slides

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
`docs/_build/talks/overview-slides/`. Generated files are ignored, not committed.
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

## Talk length and running order

The main talk has **10 slides**, including the title and summary, with a
**17-minute** target pace for a 15–20 minute slot. An **optional two-minute demo**
follows the summary, bringing the total to 19 minutes if time allows.
The source comments contain per-slide timing and a shorter 15-minute route
that skips the demo.

1. Title
2. What is Rook?
3. Processing capabilities (formerly A1)
4. Rook in CDS today
5. Rook Broker for ESGF-NG
6. A workflow with Rooki (formerly A2)
7. Workflow submission (formerly A3)
8. Deployment today and tomorrow (formerly C1)
9. Support for S3 (formerly F1)
10. Summary
11. Optional demo (Rooki on Binder and nbviewer, plus a CDS screenshot and website link)

The demo embeds the public CDS homepage screenshot, so it can be shown offline
or from another laptop without a CDS login. Use nbviewer if Binder is unavailable.

The remaining appendix keeps its B, D and E labels for reference during
questions. The broker API and container deployment remain proposals, and S3
support remains work in progress.

## Preview

```bash
make prepare
sh ./quarto.sh preview ../_build/talks/overview-slides/slides.qmd
```

Rerun `make prepare` after editing the source. Press **S** in the preview for
speaker view. Check slide fit, diagrams and links before presenting.
