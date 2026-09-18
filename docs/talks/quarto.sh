#!/bin/sh
# Conda's Quarto uses separate tool packages rather than bundled binaries.
# Set paths even immediately after installation, before shell reactivation.
set -eu

if ! command -v quarto >/dev/null 2>&1; then
    echo "Slides: Quarto is missing. Activate rook and run 'make install'." >&2
    exit 1
fi

if [ -n "${CONDA_PREFIX:-}" ] && [ "$(command -v quarto)" = "$CONDA_PREFIX/bin/quarto" ]; then
    export QUARTO_DENO="$CONDA_PREFIX/bin/deno"
    export QUARTO_PANDOC="$CONDA_PREFIX/bin/pandoc"
    export QUARTO_ESBUILD="$CONDA_PREFIX/bin/esbuild"
    export QUARTO_TYPST="$CONDA_PREFIX/bin/typst"
    export QUARTO_DART_SASS="$CONDA_PREFIX/bin/sass"
    export QUARTO_SHARE_PATH="$CONDA_PREFIX/share/quarto"
    export QUARTO_CONDA_PREFIX="$CONDA_PREFIX"
    # Some conda-forge activation hooks retain the package builder's path.
    if [ "$(uname)" = Darwin ]; then
        export QUARTO_DENO_DOM="$CONDA_PREFIX/lib/deno_dom.dylib"
    else
        export QUARTO_DENO_DOM="$CONDA_PREFIX/lib/deno_dom.so"
    fi
fi

exec quarto "$@"
