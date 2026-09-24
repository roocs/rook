# Slide setup

Add slide tools to the existing `rook` Conda environment. From the repository root:

```bash
conda activate rook
cd docs/talks
make install       # Quarto and Node.js; enough for HTML
# make install-pdf # Also install DeckTape and Chrome for PDF
make slides-html
make slides-pptx   # PowerPoint: five main slides, without the appendix
```

These targets add packages to `rook`; they do not create a new environment.
Conda packages are listed in [environment.yml](environment.yml); DeckTape uses npm.
Build targets do not install packages.
`quarto.sh` supplies Conda tool paths and reuses DeckTape's headless browser.
SVG rendering needs Chrome/Chromium even for HTML. If neither it nor DeckTape
is installed, run `sh ./quarto.sh install chrome-headless-shell` once.

Edit [Milano 2026](milano-2026/slides.qmd) or
[Architecture](architecture/slides.qmd) directly. These `.qmd` files are the
canonical presentation sources; there is no Markdown conversion step.
`make slides` renders both decks. See [Milano 2026](milano-2026/README.md)
for the optional PowerPoint export.

## Documentation publishing

`make build-docs` from the repository root builds the Sphinx documentation and
both HTML/PDF presentations. Install the PDF toolchain above first.
Read the Docs and the docs testing workflow install it automatically.

The Read the Docs pre-build hook runs `make -C docs/talks publish`.
That target builds HTML/PDF and stages only the standalone HTML (`index.html`)
and PDF under `docs/_build/published/talks/<talk>/`. Sphinx's
`html_extra_path` copies them into the documentation output. The Talks page
links to `talks/<talk>/index.html` and `talks/<talk>/slides.pdf`,
relative to the current documentation version. PowerPoint, source files,
templates and QA images are not staged or published.

The same staging target works before a direct Sphinx build:

```bash
make -C docs/talks publish
sphinx-build -b html docs/source docs/_build/html
```

On hosted Linux builders, `DECKTAPE_FLAGS=--chrome-arg=--no-sandbox` disables
Chromium's sandbox for PDF export. Normal local builds retain the default.
