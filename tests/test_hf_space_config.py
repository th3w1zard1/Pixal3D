import tempfile
import unittest
from pathlib import Path


class HuggingFaceSpaceConfigTests(unittest.TestCase):
    def test_resolve_space_config_uses_pixal3d_defaults(self):
        from scripts.resolve_hf_space_config import resolve_space_config

        config = resolve_space_config({})

        self.assertEqual(config.repo_id, "th3w1zard1/Pixal3D")
        self.assertEqual(config.repo_namespace, "th3w1zard1")
        self.assertEqual(config.repo_name, "Pixal3D")
        self.assertEqual(config.space_sdk, "gradio")

    def test_resolve_space_config_honors_repo_id_override(self):
        from scripts.resolve_hf_space_config import resolve_space_config

        config = resolve_space_config(
            {
                "HF_SPACE_REPO_ID": "custom-org/custom-space",
                "HF_SPACE_SDK": "docker",
            }
        )

        self.assertEqual(config.repo_id, "custom-org/custom-space")
        self.assertEqual(config.repo_namespace, "custom-org")
        self.assertEqual(config.repo_name, "custom-space")
        self.assertEqual(config.space_sdk, "docker")

    def test_write_github_outputs_emits_expected_keys(self):
        from scripts.resolve_hf_space_config import (
            resolve_space_config,
            write_github_outputs,
        )

        config = resolve_space_config(
            {"HF_SPACE_NAMESPACE": "pixal", "HF_SPACE_NAME": "demo"}
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "github-output.txt"
            write_github_outputs(config, str(output_path))

            content = output_path.read_text(encoding="utf-8")

        self.assertIn("repo_id=pixal/demo", content)
        self.assertIn("repo_name=demo", content)
        self.assertIn("repo_namespace=pixal", content)
        self.assertIn("space_sdk=gradio", content)


class HuggingFaceSpaceEnsureTests(unittest.TestCase):
    def test_resolve_ensure_settings_requires_token(self):
        from scripts.ensure_hf_space import resolve_ensure_settings

        with self.assertRaisesRegex(RuntimeError, "HF_TOKEN is required"):
            resolve_ensure_settings({})

    def test_resolve_ensure_settings_honors_flags(self):
        from scripts.ensure_hf_space import resolve_ensure_settings

        settings = resolve_ensure_settings(
            {
                "HF_TOKEN": "hf_test_token",
                "HF_SPACE_REPO_ID": "custom-org/custom-space",
                "HF_SPACE_SDK": "docker",
                "HF_SPACE_PRIVATE": "1",
                "HF_SPACE_CREATE_IF_MISSING": "0",
            }
        )

        self.assertEqual(settings["repo_id"], "custom-org/custom-space")
        self.assertEqual(settings["sdk"], "docker")
        self.assertTrue(settings["private"])
        self.assertFalse(settings["create_if_missing"])
