"""Checks for the commit guard; fixtures are synthetic, never real credentials."""

import sys
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_private


class PrivateCheckTests(unittest.TestCase):
    def test_known_token_shapes_are_rejected(self):
        self.assertEqual(check_private.check_content(b"glpat-" + b"X" * 24), "GitLab token")
        header = b"-----BEGIN " + b"OPENSSH " + b"PRIVATE KEY-----"
        self.assertEqual(check_private.check_content(header), "private key")

    def test_named_credential_assignment_is_rejected(self):
        self.assertEqual(
            check_private.check_content(b'{"CERNGITLAB_' + b'TOKEN": "' + b'synthetic-value-123456"}'),
            "credential assignment",
        )
        self.assertEqual(
            check_private.check_content(b"ACCESS_TOKEN=synthetic_value_123456"),
            "credential assignment",
        )

    def test_examples_are_allowed(self):
        self.assertIsNone(check_private.check_content(b'{"API_KEY": "${API_KEY}"}'))
        self.assertIsNone(check_private.check_content(b"pattern = '\\bsk-[A-Za-z0-9]{48}\\b'"))

    def test_credential_paths_are_rejected(self):
        for path in ("settings/.env.local", "keys/id_ed25519", "config/mac/cli/opencode/config.json", "config/mac/cli/opencode/opencode.jsonc", "config/mac/ssh/config.local"):
            self.assertIsNotNone(check_private.check_path(path))
        self.assertIsNone(check_private.check_path("settings/.env.example"))

    def test_hook_blocks_staged_secret_without_displaying_value(self):
        with tempfile.TemporaryDirectory(prefix="dotfiles-private-check-") as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            (root / ".githooks").mkdir()
            shutil.copy2(Path(check_private.__file__), root / "scripts/check_private.py")
            shutil.copy2(Path(__file__).resolve().parents[1] / ".githooks/pre-commit", root / ".githooks/pre-commit")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            value = "synthetic" + "_value_123456"
            (root / "settings.txt").write_text("ACCESS_TOKEN=" + value + "\n")
            subprocess.run(["git", "add", "settings.txt"], cwd=root, check=True)
            result = subprocess.run(
                [str(root / ".githooks/pre-commit")], cwd=root,
                text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("settings.txt: credential assignment", result.stdout)
            self.assertNotIn(value, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
