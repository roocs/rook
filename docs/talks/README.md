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

See [Milano 2026](milano-2026/README.md) for build and preview commands.
The talks Makefile is independent of the root Makefile and Sphinx.
