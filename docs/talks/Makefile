# Presentation builds are independent of the root development Makefile.
# Invoke with make -C docs/talks, or run make from this directory.
TALKS_DIR := $(CURDIR)
SLIDES_DIR := $(TALKS_DIR)/../_build/talks/milano-2026

.DEFAULT_GOAL := help
.PHONY: help

help: ## list presentation build targets
	@echo "Milano 2026 presentation targets:"
	@echo "  slides-html   Build Reveal.js HTML"
	@echo "  slides-pdf    Build HTML and export PDF with DeckTape"
	@echo "  slides        Build HTML and PDF"
	@echo "  slides-clean  Remove only the Milano generated output"
	@echo "  install       Add HTML tools to the existing rook environment"
	@echo "  install-pdf   Add HTML tools, DeckTape and Chrome to rook"

.PHONY: install install-pdf check-conda

check-conda:
	@command -v conda >/dev/null 2>&1 || { echo "Slides: conda is missing. Install Conda and add it to PATH first." >&2; exit 1; }

install: check-conda ## add HTML tools to the existing rook environment
	@conda run --name rook python --version || { echo "Slides: the existing rook environment with Python is required; no environment was created." >&2; exit 1; }
	conda env update --name rook --file "$(TALKS_DIR)/environment.yml"
	conda run --no-capture-output --name rook quarto --version
	conda run --no-capture-output --name rook node --version

install-pdf: install ## add the PDF exporter and its browser
	conda run --no-capture-output --name rook sh -c 'npm install --global --prefix "$$CONDA_PREFIX" decktape@3.16.1'
	conda run --no-capture-output --name rook decktape --version

.PHONY: slides-html slides-pdf slides slides-clean

slides-html: ## generate the Milano Reveal.js presentation
	python "$(TALKS_DIR)/milano-2026/build_slides.py"
	@command -v quarto >/dev/null 2>&1 || { echo "Slides: Quarto is missing. Install Quarto and add it to PATH (see docs/talks/milano-2026/README.md)." >&2; exit 1; }
	quarto render "$(SLIDES_DIR)/slides.qmd" --to revealjs

slides-pdf: slides-html ## export the Milano slides with DeckTape
	@if command -v decktape >/dev/null 2>&1; then \
		decktape reveal --size 1600x900 --load-pause 2000 "$(SLIDES_DIR)/slides.html" "$(SLIDES_DIR)/slides.pdf"; \
	elif command -v npx >/dev/null 2>&1; then \
		npx --offline --no-install decktape --version >/dev/null 2>&1 || { echo "Slides: npx cannot run an existing DeckTape. Install DeckTape explicitly first; the build never downloads packages." >&2; exit 1; }; \
		npx --offline --no-install decktape reveal --size 1600x900 --load-pause 2000 "$(SLIDES_DIR)/slides.html" "$(SLIDES_DIR)/slides.pdf"; \
	else \
		echo "Slides: DeckTape is missing. Install decktape, or Node/npm with an existing DeckTape available to npx." >&2; exit 1; \
	fi

slides: slides-pdf ## build both Milano HTML and PDF slides

slides-clean: ## remove only generated Milano presentation files
	rm -rf "$(SLIDES_DIR)/"
