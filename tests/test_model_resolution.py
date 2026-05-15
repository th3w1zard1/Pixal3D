import json
import tempfile
import unittest
from pathlib import Path


class ModelResolutionTests(unittest.TestCase):
    def test_candidate_models_deduplicate_primary_and_fallbacks(self):
        from space_bootstrap import RuntimeConfig, candidate_rembg_models

        runtime_config = RuntimeConfig(
            rembg_model="ZhengPeng7/BiRefNet",
            rembg_fallback_models=(
                "ZhengPeng7/BiRefNet_lite",
                "ZhengPeng7/BiRefNet",
            ),
        )

        self.assertEqual(
            candidate_rembg_models(runtime_config),
            ["ZhengPeng7/BiRefNet", "ZhengPeng7/BiRefNet_lite"],
        )

    def test_replaces_gated_bria_model_with_public_birefnet(self):
        from space_bootstrap import RuntimeConfig, apply_pipeline_overrides

        original = {
            "args": {
                "rembg_model": {
                    "name": "BiRefNet",
                    "args": {"model_name": "briaai/RMBG-2.0"},
                }
            }
        }

        runtime_config = RuntimeConfig(
            rembg_model="ZhengPeng7/BiRefNet",
            rembg_fallback_models=("ZhengPeng7/BiRefNet_lite",),
        )

        patched = apply_pipeline_overrides(original, runtime_config)

        self.assertEqual(
            patched["args"]["rembg_model"]["args"]["model_name"],
            "ZhengPeng7/BiRefNet",
        )
        self.assertEqual(
            original["args"]["rembg_model"]["args"]["model_name"],
            "briaai/RMBG-2.0",
        )

    def test_prepare_pipeline_directory_writes_patched_pipeline_json(self):
        from space_bootstrap import RuntimeConfig, prepare_pipeline_directory

        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "pipeline.json"
            source_path.write_text(
                json.dumps(
                    {
                        "name": "Pixal3DImageTo3DPipeline",
                        "args": {
                            "rembg_model": {
                                "name": "BiRefNet",
                                "args": {"model_name": "briaai/RMBG-2.0"},
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            def fake_download(repo_id, filename, **kwargs):
                self.assertEqual(repo_id, "TencentARC/Pixal3D-T")
                self.assertEqual(filename, "pipeline.json")
                return str(source_path)

            runtime_config = RuntimeConfig(
                rembg_model="ZhengPeng7/BiRefNet",
                rembg_fallback_models=("ZhengPeng7/BiRefNet_lite",),
            )

            resolved_dir = prepare_pipeline_directory(
                "TencentARC/Pixal3D-T",
                runtime_config,
                download_file=fake_download,
            )

            resolved_config = json.loads(
                Path(resolved_dir, "pipeline.json").read_text(encoding="utf-8")
            )

        self.assertEqual(
            resolved_config["args"]["rembg_model"]["args"]["model_name"],
            "ZhengPeng7/BiRefNet",
        )
