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

See [Milano 2026](milano-2026/README.md) for build and preview commands.

## Documentation publishing

`make build-docs` from the repository root builds the Sphinx documentation and
the HTML/PDF presentation. Install the PDF toolchain above first.
Read the Docs and the docs testing workflow install it automatically.

The Read the Docs pre-build hook runs `make -C docs/talks publish`.
That target builds HTML/PDF and stages only the standalone HTML (`index.html`)
and PDF in `docs/_build/published/talks/milano-2026/`. Sphinx's
`html_extra_path` copies them into the documentation output. The Talks page
links to `talks/milano-2026/index.html` and `talks/milano-2026/slides.pdf`,
relative to the current documentation version. PowerPoint, source files,
templates and QA images are not staged or published.

The same staging target works before a direct Sphinx build:

```bash
make -C docs/talks publish
sphinx-build -b html docs/source docs/_build/html
```

On hosted Linux builders, `DECKTAPE_FLAGS=--chrome-arg=--no-sandbox` disables
Chromium's sandbox for PDF export. Normal local builds retain the default.
