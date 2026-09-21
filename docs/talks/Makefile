# Presentation builds are independent of the root development Makefile.
# Invoke with make -C docs/talks, or run make from this directory.
TALKS_DIR := $(CURDIR)
SLIDES_DIR := $(TALKS_DIR)/../_build/talks/milano-2026
PPTX_TEMPLATE ?= $(wildcard $(TALKS_DIR)/templates/futura_black.potx)
PPTX_TEMPLATE_ARGS = $(if $(PPTX_TEMPLATE),--template "$(PPTX_TEMPLATE)")

.DEFAULT_GOAL := help
.PHONY: help

help: ## list presentation build targets
	@echo "Milano 2026 presentation targets:"
	@echo "  slides-html   Build Reveal.js HTML"
	@echo "  slides-pdf    Build HTML and export PDF with DeckTape"
	@echo "  slides-pptx   Build five main slides as editable PowerPoint"
	@echo "  slides        Build HTML and PDF"
	@echo "  slides-clean  Remove only the Milano generated output"
	@echo "  install       Add HTML tools to the existing rook environment"
	@echo "  install-pdf   Add HTML tools, DeckTape and Chrome to rook"

.PHONY: install install-pdf check-rook

check-rook:
	@command -v conda >/dev/null 2>&1 || { echo "Slides: conda is missing. Install Conda and add it to PATH first." >&2; exit 1; }
	@test "$$CONDA_DEFAULT_ENV" = rook && test -n "$$CONDA_PREFIX" || { echo "Slides: run 'conda activate rook' before installing slide tools." >&2; exit 1; }

install: check-rook ## add HTML tools to the active rook environment
	conda env update --name rook --file "$(TALKS_DIR)/environment.yml"
	sh "$(TALKS_DIR)/quarto.sh" --version
	node --version

install-pdf: install ## add the PDF exporter and its browser
	npm install --global --prefix "$$CONDA_PREFIX" decktape@3.16.1
	"$$CONDA_PREFIX/bin/decktape" version

.PHONY: slides-html slides-pdf slides-pptx slides slides-clean

slides-html: ## generate the Milano Reveal.js presentation
	python "$(TALKS_DIR)/milano-2026/build_slides.py"
	sh "$(TALKS_DIR)/quarto.sh" render "$(SLIDES_DIR)/slides.qmd" --to revealjs

slides-pptx: ## export only the main Milano slides, without the appendix
	python "$(TALKS_DIR)/milano-2026/build_slides.py" --main-only $(PPTX_TEMPLATE_ARGS)
	cd "$(SLIDES_DIR)" && sh "$(TALKS_DIR)/quarto.sh" render slides-main.qmd --to pptx --output slides-raw.pptx
	python "$(TALKS_DIR)/milano-2026/style_pptx.py" "$(SLIDES_DIR)/slides-raw.pptx" "$(SLIDES_DIR)/slides.pptx" $(PPTX_TEMPLATE_ARGS)

slides-pdf: slides-html ## export the Milano slides with DeckTape
	@if command -v decktape >/dev/null 2>&1; then \
		decktape reveal --size 1600x900 --load-pause 2000 --pause 1000 "$(SLIDES_DIR)/slides.html" "$(SLIDES_DIR)/slides.pdf"; \
	elif command -v npx >/dev/null 2>&1; then \
		npx --offline --no-install decktape version >/dev/null 2>&1 || { echo "Slides: npx cannot run an existing DeckTape. Install DeckTape explicitly first; the build never downloads packages." >&2; exit 1; }; \
		npx --offline --no-install decktape reveal --size 1600x900 --load-pause 2000 --pause 1000 "$(SLIDES_DIR)/slides.html" "$(SLIDES_DIR)/slides.pdf"; \
	else \
		echo "Slides: DeckTape is missing. Install decktape, or Node/npm with an existing DeckTape available to npx." >&2; exit 1; \
	fi

slides: slides-pdf ## build both Milano HTML and PDF slides

slides-clean: ## remove only generated Milano presentation files
	rm -rf "$(SLIDES_DIR)/"
