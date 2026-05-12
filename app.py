"""
Pixal3D HF Space Proxy
======================
This is a lightweight proxy app for HF Space that redirects users to a 
locally deployed Gradio share link.

Setup:
1. Deploy this as your HF Space app.py
2. Set HF Space Secret: REMOTE_URL = your local share link (e.g. https://xxxxx.gradio.live)
3. Users visiting the HF Space will be seamlessly redirected to your local instance.

To update the share link:
- Go to HF Space Settings -> Variables and secrets -> Update REMOTE_URL
"""

import os
import gradio as gr

REMOTE_URL = os.environ.get("REMOTE_URL", "")
GPU_NAME = os.environ.get("GPU_NAME", "")

PROXY_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pixal3D | AI Image-to-3D</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0b0f1a;
            color: #f1f5f9;
            height: 100%;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}
        .header {{
            padding: 8px 24px;
            background: rgba(22, 28, 45, 0.9);
            border-bottom: 1px solid rgba(255,255,255,0.08);
            display: flex;
            align-items: center;
            gap: 16px;
            backdrop-filter: blur(12px);
        }}
        .header h1 {{
            font-size: 16px;
            font-weight: 700;
            background: linear-gradient(135deg, #818cf8, #10b981);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            white-space: nowrap;
        }}
        .header .notice {{
            flex: 1;
            font-size: 12px;
            color: #fbbf24;
            text-align: center;
        }}
        .status {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: #94a3b8;
            white-space: nowrap;
        }}
        .status-dot {{
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: {status_color};
            animation: {status_anim};
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.4; }}
        }}
        .iframe-container {{
            flex: 1;
            position: relative;
        }}
        .iframe-container iframe {{
            width: 100%;
            height: 100%;
            border: none;
            position: absolute;
            top: 0;
            left: 0;
        }}
        .no-url {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 40px;
        }}
        .no-url-card {{
            max-width: 560px;
            background: rgba(22, 28, 45, 0.8);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 48px;
            text-align: center;
        }}
        .no-url-card h2 {{
            font-size: 24px;
            margin-bottom: 16px;
        }}
        .no-url-card p {{
            color: #94a3b8;
            line-height: 1.7;
            margin-bottom: 12px;
        }}
        .no-url-card code {{
            background: rgba(129, 140, 248, 0.15);
            color: #818cf8;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 13px;
        }}
        .link-bar {{
            padding: 8px 24px;
            background: rgba(16, 185, 129, 0.08);
            border-top: 1px solid rgba(16, 185, 129, 0.2);
            font-size: 12px;
            color: #94a3b8;
            text-align: center;
        }}
        .link-bar a {{
            color: #10b981;
            text-decoration: none;
        }}
        .link-bar a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Pixal3D</h1>
        <span class="notice"></span>
        <div class="status">
            <div class="status-dot"></div>
            <span>{status_text}</span>
        </div>
    </div>
    {content}
</body>
</html>
"""


def build_page():
    if REMOTE_URL:
        status_color = "#10b981"
        status_anim = "pulse 2s infinite"
        status_text = "Connected to remote GPU instance"
        content = f"""
        <div class="no-url">
            <div class="no-url-card">
                <h2>🚀 Redirecting to Pixal3D...</h2>
                <p style="color:#fbbf24; margin-bottom:12px;">⚠️ Due to a temporary HuggingFace error, this Space is currently unavailable. We have prepared a temporary locally-deployed instance for you.</p>
                <p style="color:#f59e0b; margin-bottom:12px;">⚡ All users share a single GPU — requests are queued. Please be patient.</p>
                <p>You will be redirected automatically.</p>
                <p style="margin-top:16px;">
                    <a href="{REMOTE_URL}" target="_blank" rel="noopener noreferrer" style="display:inline-block; padding:12px 32px; background:linear-gradient(135deg,#818cf8,#10b981); color:#fff; border-radius:8px; text-decoration:none; font-weight:600; font-size:15px;">
                        Click here if not redirected
                    </a>
                </p>
                <p style="margin-top:16px; font-size:12px; color:#64748b;">Target: <code>{REMOTE_URL}</code></p>
            </div>
        </div>
        <script>
            // Auto redirect in new tab after a short delay
            setTimeout(function() {{
                window.open("{REMOTE_URL}", "_blank");
            }}, 1500);
        </script>
        """
    else:
        status_color = "#ef4444"
        status_anim = "pulse 1.5s infinite"
        status_text = "Remote instance not configured"
        content = """
        <div class="no-url">
            <div class="no-url-card">
                <h2>⚡ Remote GPU Instance Not Connected</h2>
                <p>This Space acts as a proxy to a locally-deployed Pixal3D instance running on a dedicated GPU.</p>
                <p>To connect, set the <code>REMOTE_URL</code> secret in this Space's settings to your Gradio share link.</p>
                <p style="margin-top:24px; font-size:13px;">
                    Example: <code>https://abcdef123456.gradio.live</code>
                </p>
            </div>
        </div>
        """

    return PROXY_HTML.format(
        status_color=status_color,
        status_anim=status_anim,
        status_text=status_text,
        gpu_name=GPU_NAME,
        content=content,
    )


# Use a simple Gradio Blocks app with HTML component
with gr.Blocks(
    title="Pixal3D | AI Image-to-3D",
    css="footer {display:none !important;} .gradio-container {padding:0 !important; max-width:100% !important; height:100vh !important; overflow:hidden !important;} #proxy-frame {height:100%; max-height:100vh; padding:0; overflow:hidden;}",
    theme=gr.themes.Base(),
) as demo:
    gr.HTML(build_page(), elem_id="proxy-frame")

if __name__ == "__main__":
    demo.launch(share=True)
