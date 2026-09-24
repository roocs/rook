#!/bin/sh
# Conda's Quarto uses separate tool packages rather than bundled binaries.
# Set paths even immediately after installation, before shell reactivation.
set -eu

if ! command -v quarto >/dev/null 2>&1; then
    echo "Slides: Quarto is missing. Activate rook and run 'make install'." >&2
    exit 1
fi

# RTD can add the environment's bin directory to PATH without activating it.
# Locate the installation actually selected on PATH, not a missing/stale
# CONDA_PREFIX inherited from the build runner.
quarto_executable=$(command -v quarto)
quarto_prefix=$(CDPATH= cd -- "$(dirname -- "$quarto_executable")/.." && pwd -P)
if [ -d "$quarto_prefix/conda-meta" ] && [ -d "$quarto_prefix/share/quarto" ]; then
    export QUARTO_DENO="$quarto_prefix/bin/deno"
    export QUARTO_PANDOC="$quarto_prefix/bin/pandoc"
    export QUARTO_ESBUILD="$quarto_prefix/bin/esbuild"
    export QUARTO_TYPST="$quarto_prefix/bin/typst"
    export QUARTO_DART_SASS="$quarto_prefix/bin/sass"
    export QUARTO_SHARE_PATH="$quarto_prefix/share/quarto"
    export QUARTO_CONDA_PREFIX="$quarto_prefix"
    # Some conda-forge activation hooks retain the package builder's path.
    if [ "$(uname)" = Darwin ]; then
        export QUARTO_DENO_DOM="$quarto_prefix/lib/deno_dom.dylib"
    else
        export QUARTO_DENO_DOM="$quarto_prefix/lib/deno_dom.so"
    fi
fi

# Prefer DeckTape's already-installed headless browser for SVG rendering.
# Respect an explicit browser override; never download a browser during builds.
if [ -z "${QUARTO_CHROMIUM:-}" ] && command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    quarto_browser=$(node -e '
        const {createRequire} = require("node:module");
        const load = createRequire(process.argv[1] + "/decktape/package.json");
        console.log(load("puppeteer").executablePath({headless: "shell"}));
    ' "$(npm root --global)" 2>/dev/null) || quarto_browser=""
    if [ -x "$quarto_browser" ]; then
        export QUARTO_CHROMIUM="$quarto_browser"
    fi
fi

exec "$quarto_executable" "$@"
