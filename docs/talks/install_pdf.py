"""Install the PDF toolchain into the running Python environment."""

import shutil
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- invoke npm with an argument list
import sys


def main():
    """Avoid nested shell quoting and dependence on Conda activation variables."""
    npm = shutil.which("npm")
    if npm is None:
        raise SystemExit("Slides: npm is missing; install the slide environment first.")
    subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] -- npm resolved from PATH
        [npm, "install", "--global", "--prefix", sys.prefix, "decktape@3.16.1"],
        check=True,
    )


if __name__ == "__main__":
    main()
