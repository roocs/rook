# Slide setup

Add slide tools to the existing `rook` Conda environment. From the repository root:

```bash
conda activate rook
cd docs/talks
make install       # Quarto, Node.js and MkDocs
# make install-pdf # Also install DeckTape and Chrome for PDF
make slides-html
```

These targets add packages to `rook`; they do not create a new environment.
Conda packages are listed in [environment.yml](environment.yml); DeckTape uses npm.
Build targets do not install packages.
`quarto.sh` supplies Conda tool paths and reuses DeckTape's headless browser.
It finds the Conda prefix from the Quarto executable on `PATH`, without depending on
shell activation hooks or `CONDA_PREFIX`.
SVG rendering needs Chrome/Chromium even for HTML. If neither it nor DeckTape
is installed, run `sh ./quarto.sh install chrome-headless-shell` once.

Edit [Milano 2026](milano-2026/slides.qmd) or
[Architecture](architecture/slides.qmd) directly. These `.qmd` files are the
canonical presentation sources; there is no Markdown conversion step.
`make slides` renders both decks as HTML and PDF. See
[Milano 2026](milano-2026/README.md) for preview instructions.

## Separate documentation and slides sites

The service documentation stays on Sphinx and Read the Docs:
<https://rook-wps.readthedocs.io/en/latest/>. `make build-docs` and the
`Build Sphinx docs` workflow build only those docs. They do not install or run
Quarto, Node, Chrome, DeckTape or MkDocs.

The slides site uses MkDocs Material and GitHub Pages:
<https://roocs.github.io/rook/>. It links back to the RTD docs; the Sphinx Talks
page links to the HTML decks and PDFs here. Milano's architecture references
also point to this site.

After installing the slide/PDF tools above, run from the repository root:

```bash
make -C docs/talks publish
python -m http.server 8000 --directory site
```

Open <http://localhost:8000/>. The `publish` target renders both decks as HTML
and PDF, builds `mkdocs-slides.yml`, then copies only `index.html` and
`slides.pdf` into `site/talks/<talk>/`. The landing page is maintained in
`docs/talks/site_src/index.md`. Sources, templates, PowerPoint and QA images
are never copied into the site. `check_published.py` verifies the files and
new-tab links after every build.

The separate `Build and deploy slides` workflow uses only the slide environment
and `requirements.txt`, without installing the Rook service. Pull requests,
pushes to `main`, and manual runs build the site and upload a `slides-site`
preview artifact. Successful `main` builds deploy to GitHub Pages using the
`github-pages` environment. Pull requests never deploy.

For the first deployment, set repository **Settings → Pages → Build and
deployment → Source** to **GitHub Actions**. No extra deployment token is
needed. The published URLs are:

- Milano: `https://roocs.github.io/rook/talks/milano-2026/index.html`
- Architecture: `https://roocs.github.io/rook/talks/architecture/index.html`
- Each PDF: replace `index.html` with `slides.pdf`.

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
Share it separately if needed. Keep the `publish` target limited to HTML/PDF and the Read the Docs
configuration limited to Sphinx documentation.
