# Pixal3D Agent Notes

- When a task touches Hugging Face Spaces, ZeroGPU, Gradio, `hf`, or browser-to-backend transport, look up current official docs with Context7 before changing code.
- For this repo's hosted ZeroGPU path, preserve browser calls through `@gradio/client` unless current docs explicitly say another browser transport is supported for `Server` apps on ZeroGPU.
- Do not add regression or unit tests for runtime or UI fixes in this repo unless the user explicitly asks for tests.
- Do not declare a hosted Space fix complete from source edits alone.
- If runtime-facing files changed and there is no conflicting unrelated local work in those same files, deploy the candidate change to the test Space with the `hf` CLI.
- After deploy, verify the live Space in a browser and run one end-to-end check with a default sample image before closing the task.
- If deployment is unsafe because the working tree contains unrelated runtime changes, say so explicitly instead of silently publishing them.
