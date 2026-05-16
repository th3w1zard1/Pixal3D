import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock


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
    def test_ensure_space_returns_false_when_space_exists(self):
        from scripts.ensure_hf_space import ensure_space

        api = Mock()

        created = ensure_space(api, "custom-org/custom-space", "gradio")

        self.assertFalse(created)
        api.repo_info.assert_called_once_with(
            repo_id="custom-org/custom-space",
            repo_type="space",
        )
        api.create_repo.assert_not_called()

    def test_ensure_space_creates_repo_after_not_found(self):
        from scripts.ensure_hf_space import ensure_space

        api = Mock()
        response = type("Response", (), {"status_code": 404})()
        api.repo_info.side_effect = Exception("missing")
        api.repo_info.side_effect.response = response

        created = ensure_space(
            api,
            "custom-org/custom-space",
            "docker",
            private=True,
            create_if_missing=True,
        )

        self.assertTrue(created)
        api.create_repo.assert_called_once_with(
            repo_id="custom-org/custom-space",
            repo_type="space",
            private=True,
            exist_ok=True,
            space_sdk="docker",
        )

    def test_ensure_space_raises_forbidden_as_permission_error(self):
        from scripts.ensure_hf_space import ensure_space

        api = Mock()
        response = type("Response", (), {"status_code": 403})()
        error = Exception("forbidden")
        error.response = response
        api.repo_info.side_effect = error

        with self.assertRaisesRegex(RuntimeError, "verify HF_TOKEN permissions"):
            ensure_space(api, "custom-org/custom-space", "gradio")

        api.create_repo.assert_not_called()

    def test_ensure_space_raises_when_missing_and_creation_disabled(self):
        from scripts.ensure_hf_space import ensure_space

        api = Mock()
        response = type("Response", (), {"status_code": 404})()
        error = Exception("missing")
        error.response = response
        api.repo_info.side_effect = error

        with self.assertRaisesRegex(RuntimeError, "Space does not exist"):
            ensure_space(
                api,
                "custom-org/custom-space",
                "gradio",
                create_if_missing=False,
            )

        api.create_repo.assert_not_called()

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
