"""Exercise Quarto startup without relying on Conda shell activation."""

import os
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- execute the local wrapper with fake tools
import tempfile
import unittest
from pathlib import Path

WRAPPER = Path(__file__).resolve().parents[2] / "docs/talks/quarto.sh"


class QuartoEnvironmentTests(unittest.TestCase):
    """Cover PATH-only RTD environments and native Quarto installations."""

    def test_conda_tools_without_activation(self):
        """Use the selected executable's prefix even with missing or stale activation."""
        for platform, library in (("Linux", "deno_dom.so"), ("Darwin", "deno_dom.dylib")):
            for active_prefix in (None, "/unrelated/base/environment"):
                with self.subTest(platform=platform, active_prefix=active_prefix):
                    self.check_environment(platform, library, active_prefix)

    def check_environment(self, platform, library, active_prefix):
        """Run a fake Conda Quarto and inspect the environment passed to it."""
        with tempfile.TemporaryDirectory(prefix="rook quarto ") as directory:
            prefix = Path(directory)
            (prefix / "bin").mkdir()
            (prefix / "conda-meta").mkdir()
            (prefix / "share/quarto").mkdir(parents=True)
            for name, body in (("quarto", 'env\nprintf "ARG=%s\\n" "$@"'), ("uname", f"echo {platform}")):
                executable = prefix / "bin" / name
                executable.write_text("#!/bin/sh\n" + body + "\n")
                executable.chmod(0o755)
            env = {k: v for k, v in os.environ.items() if not k.startswith(("QUARTO_", "CONDA_"))}
            env.update(PATH=f"{prefix}/bin:/usr/bin:/bin", QUARTO_CHROMIUM="/explicit/browser", QUARTO_DENO="/stale/deno")
            if active_prefix:
                env["CONDA_PREFIX"] = active_prefix
            result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] -- fixed local wrapper and controlled environment
                ["/bin/sh", str(WRAPPER), "--help"], env=env, capture_output=True, text=True, check=True,
            )
            output = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
            resolved = prefix.resolve()
            for variable, relative in {
                "QUARTO_DENO": "bin/deno", "QUARTO_PANDOC": "bin/pandoc",
                "QUARTO_ESBUILD": "bin/esbuild", "QUARTO_TYPST": "bin/typst",
                "QUARTO_DART_SASS": "bin/sass", "QUARTO_SHARE_PATH": "share/quarto",
                "QUARTO_DENO_DOM": f"lib/{library}",
            }.items():
                self.assertEqual(output[variable], str(resolved / relative))
            self.assertEqual(output["QUARTO_CONDA_PREFIX"], str(resolved))
            self.assertEqual(output["QUARTO_CHROMIUM"], "/explicit/browser")
            self.assertEqual(output["ARG"], "--help")

            # A non-Conda installation must retain its normal configuration.
            (prefix / "conda-meta").rmdir()
            result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] -- fixed local wrapper and controlled environment
                ["/bin/sh", str(WRAPPER), "--help"], env=env, capture_output=True, text=True, check=True,
            )
            self.assertIn("QUARTO_DENO=/stale/deno\n", result.stdout)
            self.assertNotIn("QUARTO_CONDA_PREFIX=", result.stdout)
