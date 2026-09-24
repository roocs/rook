"""Check the installer passes paths to npm without shell interpretation."""

import importlib.util
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- test npm error propagation
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "install_pdf", Path(__file__).resolve().parents[2] / "docs/talks/install_pdf.py",
)
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class InstallPdfTests(unittest.TestCase):
    """Keep the RTD and GitHub installation command free of shell quoting."""

    def test_prefix_is_passed_as_one_argument(self):
        """Spaces and shell characters in the Python prefix stay literal."""
        prefix = "/environment with spaces/it's $(not-a-command)"
        with (
            patch.object(installer.sys, "prefix", prefix),
            patch.object(installer.shutil, "which", return_value="/tools/bin/npm"),
            patch.object(installer.subprocess, "run") as run,
        ):
            installer.main()
        run.assert_called_once_with(
            ["/tools/bin/npm", "install", "--global", "--prefix", prefix, "decktape@3.16.1"],
            check=True,
        )

    def test_missing_npm(self):
        """A missing installer produces an actionable error."""
        with patch.object(installer.shutil, "which", return_value=None), self.assertRaisesRegex(SystemExit, "npm is missing"):
            installer.main()

    def test_install_failure_propagates(self):
        """An npm failure must fail the RTD build job."""
        with (
            patch.object(installer.shutil, "which", return_value="/tools/bin/npm"),
            patch.object(installer.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "npm")),
            self.assertRaises(subprocess.CalledProcessError),
        ):
            installer.main()
