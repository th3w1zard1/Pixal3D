from __future__ import annotations

import unittest


class RuntimePolicyTests(unittest.TestCase):
    def test_hosted_space_branch_uses_zerogpu_then_hosted_cpu(self):
        from runtime_policy import active_runtime_branch, active_runtime_order

        env = {"SPACE_ID": "th3w1zard1/Pixal3D"}

        self.assertEqual(active_runtime_branch(env), "space")
        self.assertEqual(active_runtime_order(env), ("zerogpu", "space_cpu"))

    def test_local_branch_uses_local_gpu_then_local_cpu(self):
        from runtime_policy import active_runtime_branch, active_runtime_order

        self.assertEqual(active_runtime_branch({}), "local")
        self.assertEqual(active_runtime_order({}), ("local_gpu", "local_cpu"))

    def test_policy_payload_keeps_all_four_rules_and_context(self):
        from runtime_policy import build_runtime_policy_payload

        payload = build_runtime_policy_payload(
            {"SPACE_ID": "th3w1zard1/Pixal3D", "ACCELERATOR": "none"},
            cuda_available=False,
        )

        self.assertEqual(
            payload["runtime_fallback_order"],
            ["zerogpu", "space_cpu", "local_gpu", "local_cpu"],
        )
        self.assertEqual(payload["runtime_policy_branch"], "space")
        self.assertEqual(
            payload["runtime_policy_active_order"], ["zerogpu", "space_cpu"]
        )
        self.assertEqual(payload["primary_runtime_key"], "zerogpu")
        self.assertEqual(payload["fallback_runtime_key"], "space_cpu")
        self.assertEqual(payload["primary_execution_device"], "cuda")
        self.assertEqual(payload["generation_primary_endpoint"], "/generate_3d")
        self.assertEqual(
            payload["generation_fallback_endpoint"], "/generate_3d_cpu_fallback"
        )
        self.assertFalse(payload["cuda_available"])
        self.assertEqual(payload["rules"][0]["key"], "zerogpu")  # pyright: ignore[reportIndexIssue]
        self.assertEqual(payload["rules"][-1]["key"], "local_cpu")  # pyright: ignore[reportIndexIssue]

    def test_local_cpu_selection_disables_preview_and_picks_cpu_device(self):
        from runtime_policy import resolve_generation_plan

        plan = resolve_generation_plan({}, cuda_available=False)

        self.assertEqual(plan["primary_rule_key"], "local_cpu")
        self.assertEqual(plan["selected_rule_key"], "local_cpu")
        self.assertEqual(plan["execution_device"], "cpu")
        self.assertFalse(plan["render_preview"])

    def test_local_gpu_selection_keeps_local_cpu_as_explicit_fallback(self):
        from runtime_policy import resolve_extraction_plan

        plan = resolve_extraction_plan({}, cuda_available=True)

        self.assertEqual(plan["primary_rule_key"], "local_gpu")
        self.assertEqual(plan["fallback_rule_key"], "local_cpu")
        self.assertEqual(plan["primary_endpoint"], "/extract_glb_api")
        self.assertEqual(plan["fallback_endpoint"], "/extract_glb_api_cpu_fallback")
