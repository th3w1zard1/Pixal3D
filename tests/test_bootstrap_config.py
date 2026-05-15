import unittest
from unittest import mock


class RuntimeConfigTests(unittest.TestCase):
    def test_build_runtime_config_disables_warmup_by_default_on_space(self):
        from space_bootstrap import build_runtime_config

        config = build_runtime_config({"SPACE_ID": "th3w1zard1/Pixal3D"})

        self.assertFalse(config.warmup_on_start)

    def test_build_runtime_config_allows_explicit_warmup_override_on_space(self):
        from space_bootstrap import build_runtime_config

        config = build_runtime_config(
            {
                "SPACE_ID": "th3w1zard1/Pixal3D",
                "PIXAL3D_WARMUP_ON_START": "1",
            }
        )

        self.assertTrue(config.warmup_on_start)

    def test_build_hf_hub_kwargs_can_skip_revision(self):
        from space_bootstrap import RuntimeConfig, build_hf_hub_kwargs

        config = RuntimeConfig(
            hf_token="hf_test_token",
            hf_cache_dir="/tmp/cache",
            pipeline_revision="rev-123",
        )

        kwargs = build_hf_hub_kwargs(config, include_revision=False)

        self.assertEqual(
            kwargs,
            {
                "token": "hf_test_token",
                "cache_dir": "/tmp/cache",
            },
        )

    def test_build_runtime_config_reads_env_overrides(self):
        from space_bootstrap import build_runtime_config

        config = build_runtime_config(
            {
                "HF_TOKEN": "hf_test_token",
                "PIXAL3D_HF_CACHE_DIR": "/tmp/pixal-cache",
                "PIXAL3D_PIPELINE_REVISION": "rev-123",
                "PIXAL3D_REMBG_MODEL": "Custom/BiRefNet",
                "PIXAL3D_REMBG_FALLBACKS": "One/Model,Two/Model",
                "PIXAL3D_REMBG_TRUST_REMOTE_CODE": "0",
                "PIXAL3D_WARMUP_ON_START": "0",
            }
        )

        self.assertEqual(config.hf_token, "hf_test_token")
        self.assertEqual(config.hf_cache_dir, "/tmp/pixal-cache")
        self.assertEqual(config.pipeline_revision, "rev-123")
        self.assertEqual(config.rembg_model, "Custom/BiRefNet")
        self.assertEqual(config.rembg_fallback_models, ("One/Model", "Two/Model"))
        self.assertFalse(config.rembg_trust_remote_code)
        self.assertFalse(config.warmup_on_start)


class RuntimeDependencyTests(unittest.TestCase):
    def test_build_launch_options_disables_share_by_default(self):
        from space_runtime import build_launch_options

        options = build_launch_options({})

        self.assertTrue(options["show_error"])
        self.assertFalse(options["share"])

    def test_build_launch_options_honors_gradio_share_env(self):
        from space_runtime import build_launch_options

        options = build_launch_options({"GRADIO_SHARE": "1"})

        self.assertTrue(options["share"])

    @mock.patch("space_runtime.subprocess.run")
    @mock.patch("space_runtime.importlib.util.find_spec", return_value=None)
    def test_ensure_utils3d_installs_only_when_missing(self, _find_spec, run):
        from space_runtime import ensure_utils3d_installed

        ensure_utils3d_installed()

        run.assert_called_once()

    @mock.patch("space_runtime.subprocess.run")
    @mock.patch("space_runtime.importlib.util.find_spec", return_value=object())
    def test_ensure_utils3d_skips_install_when_present(self, _find_spec, run):
        from space_runtime import ensure_utils3d_installed

        ensure_utils3d_installed()

        run.assert_not_called()
