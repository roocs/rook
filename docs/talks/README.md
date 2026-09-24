# Slide setup

Add slide tools to the existing `rook` Conda environment. From the repository root:

```bash
conda activate rook
cd docs/talks
make install       # Quarto and Node.js; enough for HTML
# make install-pdf # Also install DeckTape and Chrome for PDF
make slides-html
```

These targets add packages to `rook`; they do not create a new environment.
Conda packages are listed in [environment.yml](environment.yml); DeckTape uses npm.
Build targets do not install packages.
`quarto.sh` supplies Conda tool paths and reuses DeckTape's headless browser.
It finds the Conda prefix from the Quarto executable on `PATH`, so Read the Docs
does not need to run shell activation hooks or set `CONDA_PREFIX`.
SVG rendering needs Chrome/Chromium even for HTML. If neither it nor DeckTape
is installed, run `sh ./quarto.sh install chrome-headless-shell` once.

Edit [Milano 2026](milano-2026/slides.qmd) or
[Architecture](architecture/slides.qmd) directly. These `.qmd` files are the
canonical presentation sources; there is no Markdown conversion step.
`make slides` renders both decks as HTML and PDF. See
[Milano 2026](milano-2026/README.md) for preview instructions.

## Documentation publishing

`make build-docs` from the repository root builds the Sphinx documentation and
both HTML/PDF presentations. Install the PDF toolchain above first.
Read the Docs and the docs testing workflow install it automatically.

GitHub Actions builds and checks the complete site on pull requests, pushes to
`main`, and manual runs. Build or publication-check failures fail the job.
The `docs-and-slides` workflow artifact contains `docs/build/html/` for review.
Read the Docs remains the deployment host through its repository integration;
GitHub Actions does not upload to GitHub Pages or require a deployment token.
Both services run `check_published.py` to verify the HTML/PDF files and new-tab
links for every canonical talk, and reject extra files in the published talks.

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

## Emergency PowerPoint export

PowerPoint generation is no longer maintained. Normal builds and documentation
deployments include only HTML and PDF. If an editable PowerPoint is urgently
needed, the last working Quarto-based Milano exporter is preserved in commit
`c686f5b01c542dcc0fa724fd428fefa5b10afd3d`.

From the repository root, restore only its helper scripts and tests:

```bash
git restore --source=c686f5b01c542dcc0fa724fd428fefa5b10afd3d -- \
  docs/talks/milano-2026/prepare_pptx.py \
  docs/talks/milano-2026/style_pptx.py \
  docs/talks/milano-2026/template_pptx.py \
  tests/slides/test_prepare_pptx.py \
  tests/slides/test_style_pptx.py
```

In `milano-2026/slides.qmd`, add this entry under the existing `format:` key,
at the same indentation as `revealjs:`:

```yaml
  pptx:
    slide-level: 1
    mermaid-format: png
```

Activate `rook` and install the slide tools described above. Quarto and
Chrome/Chromium are required; PDF export is not needed for PowerPoint.
Then run from `docs/talks/`:

```bash
make prepare
python milano-2026/prepare_pptx.py \
  ../_build/talks/milano-2026/slides.qmd \
  ../_build/talks/milano-2026/slides-main.qmd
sh ./quarto.sh render ../_build/talks/milano-2026/slides-main.qmd \
  --to pptx --output slides-raw.pptx
python milano-2026/style_pptx.py \
  ../_build/talks/milano-2026/slides-raw.pptx \
  ../_build/talks/milano-2026/slides.pptx
pytest --confcutdir=../../tests/slides -o addopts='' ../../tests/slides
```

The exporter takes the five main Milano slides before `# Appendix`. Its layout
assumes that slide structure; later content changes may require edits to
`style_pptx.py`. It does not support the architecture deck. Text and links remain
editable, while diagrams become PNG images. Open the result in PowerPoint or
Google Slides and check every slide before presenting.

For the former Futura black styling, obtain the private one-slide reference
from Woodpecker and place it at `docs/talks/templates/futura_black.potx` (ignored
by Git). Append `--template templates/futura_black.potx` to **both** Python
commands above. The reference must have one selected slide on a 13⅓ by 7½ inch
canvas; install its fonts for matching typography. Omitting the template uses
the original light styling.

The emergency output stays in `docs/_build/talks/milano-2026/slides.pptx`.
Share it separately if needed. Keep the `publish` target and Read the Docs
configuration unchanged so deployments continue to contain only HTML and PDF.
