import unittest
import time


class ModelInitStateTests(unittest.TestCase):
    def test_start_background_initialization_runs_to_ready(self):
        from space_runtime import ModelInitState, start_background_initialization

        state = ModelInitState()
        calls = []

        def prepare_runtime():
            calls.append("prepare")

        def init_models():
            calls.append("init")

        thread = start_background_initialization(
            state,
            init_models,
            prepare_runtime=prepare_runtime,
            enabled=True,
        )
        thread.join(timeout=2)

        self.assertFalse(thread.is_alive())
        self.assertEqual(calls, ["prepare", "init"])
        self.assertEqual(state.snapshot()["state"], "ready")

    def test_start_background_initialization_skips_when_disabled(self):
        from space_runtime import ModelInitState, start_background_initialization

        state = ModelInitState()
        calls = []

        thread = start_background_initialization(
            state,
            lambda: calls.append("init"),
            prepare_runtime=lambda: calls.append("prepare"),
            enabled=False,
        )

        self.assertIsNone(thread)
        self.assertEqual(calls, [])
        self.assertEqual(state.snapshot()["state"], "pending")

    def test_run_initialization_marks_ready_after_prepare_and_init(self):
        from space_runtime import ModelInitState, run_initialization

        state = ModelInitState()
        calls = []

        def prepare_runtime():
            calls.append("prepare")

        def init_models():
            calls.append("init")

        run_initialization(state, init_models, prepare_runtime=prepare_runtime)

        self.assertEqual(calls, ["prepare", "init"])
        self.assertEqual(state.snapshot()["state"], "ready")

    def test_run_initialization_marks_error_and_reraises(self):
        from space_runtime import ModelInitState, run_initialization

        state = ModelInitState()

        def init_models():
            raise RuntimeError("boom")

        with self.assertRaisesRegex(RuntimeError, "boom"):
            run_initialization(state, init_models, prepare_runtime=lambda: None)

        self.assertEqual(state.snapshot()["state"], "error")

    def test_snapshot_reports_ready_after_successful_initialization(self):
        from space_runtime import ModelInitState

        state = ModelInitState()
        state.mark_initializing()
        state.mark_ready()

        snapshot = state.snapshot()

        self.assertTrue(snapshot["ready"])
        self.assertEqual(snapshot["state"], "ready")
        self.assertIn("ready", snapshot["message"].lower())

    def test_snapshot_reports_error_after_failed_initialization(self):
        from space_runtime import ModelInitState

        state = ModelInitState()
        state.mark_initializing()
        state.mark_error(RuntimeError("model init failed"))

        snapshot = state.snapshot()

        self.assertFalse(snapshot["ready"])
        self.assertEqual(snapshot["state"], "error")
        self.assertIn("model init failed", snapshot["message"])
