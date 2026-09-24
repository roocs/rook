# Presentation builds are independent of the root development Makefile.
# Invoke with make -C docs/talks, or run make from this directory.
TALKS_DIR := $(CURDIR)
BUILD_DIR := $(TALKS_DIR)/../_build/talks
TALKS := $(patsubst %/slides.qmd,%,$(wildcard */slides.qmd))
DECKTAPE_FLAGS ?=
PUBLISH_DIR := $(TALKS_DIR)/../_build/published/talks

.DEFAULT_GOAL := help
.PHONY: help

help: ## list presentation build targets
	@echo "Presentation targets:"
	@echo "  slides-html   Build Reveal.js HTML"
	@echo "  slides-pdf    Build HTML and export PDF with DeckTape"
	@echo "  slides        Build HTML and PDF"
	@echo "  publish       Build and stage HTML/PDF for Sphinx (no deployment)"
	@echo "  publish-html  Build and stage only HTML for Sphinx"
	@echo "  slides-clean  Remove generated talk outputs"
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
	python "$(TALKS_DIR)/install_pdf.py"
	"$$CONDA_PREFIX/bin/decktape" version

.PHONY: slides-html slides-pdf slides slides-clean

# Copy canonical sources and their assets into the ignored build tree.
# Relative paths work unchanged both in source previews and rendered copies.
.PHONY: prepare
prepare:
	@set -e; for talk in $(TALKS); do \
		mkdir -p "$(BUILD_DIR)/$$talk"; \
		cp -R "$(TALKS_DIR)/$$talk/." "$(BUILD_DIR)/$$talk/"; \
	done

slides-html: prepare ## render all canonical Quarto presentations
	@set -e; for talk in $(TALKS); do \
		sh "$(TALKS_DIR)/quarto.sh" render "$(BUILD_DIR)/$$talk/slides.qmd" --to revealjs; \
	done

slides-pdf: slides-html ## export all talks with DeckTape
	@set -e; if command -v decktape >/dev/null 2>&1; then \
		exporter=decktape; \
	elif command -v npx >/dev/null 2>&1 && npx --offline --no-install decktape version >/dev/null 2>&1; then \
		exporter="npx --offline --no-install decktape"; \
	else \
		echo "Slides: install DeckTape explicitly first; builds never download packages." >&2; exit 1; \
	fi; \
	for talk in $(TALKS); do \
		$$exporter reveal --size 1600x900 --load-pause 2000 --pause 1000 $(DECKTAPE_FLAGS) "$(BUILD_DIR)/$$talk/slides.html" "$(BUILD_DIR)/$$talk/slides.pdf"; \
	done

slides: slides-pdf ## build HTML and PDF for all talks

.PHONY: publish publish-html
publish-html: slides-html ## stage HTML only, removing previously staged PDFs
	@set -e; for talk in $(TALKS); do \
		mkdir -p "$(PUBLISH_DIR)/$$talk"; \
		cp "$(BUILD_DIR)/$$talk/slides.html" "$(PUBLISH_DIR)/$$talk/index.html"; \
		rm -f "$(PUBLISH_DIR)/$$talk/slides.pdf"; \
	done

publish: slides ## stage only standalone HTML and PDF for Sphinx
	@set -e; for talk in $(TALKS); do \
		mkdir -p "$(PUBLISH_DIR)/$$talk"; \
		cp "$(BUILD_DIR)/$$talk/slides.html" "$(PUBLISH_DIR)/$$talk/index.html"; \
		cp "$(BUILD_DIR)/$$talk/slides.pdf" "$(PUBLISH_DIR)/$$talk/slides.pdf"; \
	done

slides-clean: ## remove only generated presentation files
	rm -rf "$(BUILD_DIR)/" "$(PUBLISH_DIR)/"
