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

# Multi-instance support: REMOTE_URL as #0, REMOTE_URL_1, REMOTE_URL_2, REMOTE_URL_3
REMOTE_URLS = []
if REMOTE_URL:
    name0 = os.environ.get("REMOTE_NAME", "Instance 0")
    REMOTE_URLS.append({"url": REMOTE_URL, "name": name0})
for i in range(1, 4):
    url = os.environ.get(f"REMOTE_URL_{i}", "")
    name = os.environ.get(f"REMOTE_NAME_{i}", f"Instance {i}")
    if url:
        REMOTE_URLS.append({"url": url, "name": name})

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
        .cards-container {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px;
            overflow-y: auto;
        }}
        .cards-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 28px;
            max-width: 1000px;
            width: 100%;
        }}
        .instance-card {{
            width: 100%;
            background: rgba(22, 28, 45, 0.8);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 24px;
            padding: 60px 48px;
            text-align: center;
            transition: transform 0.2s, border-color 0.2s;
        }}
        .instance-card:hover {{
            transform: translateY(-4px);
            border-color: rgba(129, 140, 248, 0.4);
        }}
        .instance-card h3 {{
            font-size: 26px;
            margin-bottom: 16px;
            color: #f1f5f9;
        }}
        .queue-status {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 15px;
            font-weight: 600;
            margin-bottom: 8px;
            background: rgba(148, 163, 184, 0.1);
            color: #94a3b8;
        }}
        .queue-status.idle {{
            background: rgba(16, 185, 129, 0.15);
            color: #10b981;
        }}
        .queue-status.busy {{
            background: rgba(251, 146, 60, 0.15);
            color: #fb923c;
        }}
        .queue-status.offline {{
            background: rgba(239, 68, 68, 0.15);
            color: #ef4444;
        }}
        .queue-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
            animation: pulse 2s infinite;
        }}
        .instance-card .url-hint {{
            font-size: 13px;
            color: #64748b;
            margin-top: 18px;
            word-break: break-all;
        }}
        .instance-card .btn-go {{
            display: inline-block;
            margin-top: 24px;
            padding: 16px 44px;
            background: linear-gradient(135deg, #818cf8, #10b981);
            color: #ffffff !important;
            border-radius: 12px;
            text-decoration: none !important;
            font-weight: 700;
            font-size: 18px;
            transition: opacity 0.2s;
        }}
        .instance-card .btn-go:hover {{
            opacity: 0.85;
            text-decoration: none !important;
        }}
        .instance-card .btn-go:hover {{
            opacity: 0.85;
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
    # If multi-instance URLs are configured, show cards
    if REMOTE_URLS:
        status_color = "#10b981"
        status_anim = "pulse 2s infinite"
        status_text = f"{len(REMOTE_URLS)} instance(s) available"
        
        cards_html = ""
        for i, inst in enumerate(REMOTE_URLS):
            cards_html += f"""
            <div class="instance-card">
                <h3>🖥️ {inst['name']}</h3>
                <p style="color:#94a3b8; font-size:14px; margin-bottom:8px;">⚡ Shared GPU — requests are queued</p>
                <div class="queue-status" id="queue-status-{i}">
                    <span class="queue-dot"></span>
                    <span id="queue-text-{i}">Checking...</span>
                </div>
                <a href="{inst['url']}" target="_blank" rel="noopener noreferrer" class="btn-go">
                    Open Instance {i}
                </a>
                <p class="url-hint"><code>{inst['url']}</code></p>
            </div>
            """
        
        # Build JS array of instance URLs for direct polling (Gradio share links support CORS natively)
        urls_js = ", ".join(['"' + inst["url"].rstrip("/") + '"' for inst in REMOTE_URLS])
        
        content = f"""
        <div class="cards-container">
            <div style="width:100%; text-align:center; margin-bottom:16px;">
                <h2 style="font-size:28px; margin-bottom:12px;">🚀 Choose a Pixal3D Instance</h2>
                <p style="color:#fbbf24; font-size:15px; margin-bottom:8px;">⚠️ Due to a temporary HuggingFace error, this Space is currently unavailable. Please use one of the instances below.</p>
                <p style="color:#10b981; font-size:14px; margin-top:10px; font-weight:600;">💡 Choose the instance with the shortest queue!</p>
            </div>
            <div class="cards-grid">
                {cards_html}
            </div>
        </div>
        """
        
        poll_script = f"""
            const INSTANCE_URLS = [{urls_js}];
            async function pollQueues() {{
                for (let i = 0; i < INSTANCE_URLS.length; i++) {{
                    try {{
                        const controller = new AbortController();
                        const timeout = setTimeout(() => controller.abort(), 5000);
                        const resp = await fetch(INSTANCE_URLS[i] + '/queue?session_id=', {{
                            signal: controller.signal
                        }});
                        clearTimeout(timeout);
                        if (resp.ok) {{
                            const data = await resp.json();
                            const total = data.total_waiting + (data.gpu_busy ? 1 : 0);
                            const el = document.getElementById('queue-text-' + i);
                            const status = document.getElementById('queue-status-' + i);
                            if (total === 0) {{
                                el.textContent = 'Idle — no queue';
                                status.className = 'queue-status idle';
                            }} else {{
                                el.textContent = total + ' in queue';
                                status.className = 'queue-status busy';
                            }}
                        }} else {{
                            const el = document.getElementById('queue-text-' + i);
                            const status = document.getElementById('queue-status-' + i);
                            if (el) {{
                                el.textContent = 'Offline';
                                status.className = 'queue-status offline';
                            }}
                        }}
                    }} catch (e) {{
                        const el = document.getElementById('queue-text-' + i);
                        const status = document.getElementById('queue-status-' + i);
                        if (el) {{
                            el.textContent = 'Offline';
                            status.className = 'queue-status offline';
                        }}
                    }}
                }}
            }}
            pollQueues();
            setInterval(pollQueues, 5000);
        """
    else:
        status_color = "#ef4444"
        status_anim = "pulse 1.5s infinite"
        status_text = "Remote instance not configured"
        poll_script = ""
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

    html = PROXY_HTML.format(
        status_color=status_color,
        status_anim=status_anim,
        status_text=status_text,
        gpu_name=GPU_NAME,
        content=content,
    )
    return html, poll_script


# Use a simple Gradio Blocks app with HTML component
page_html, page_script = build_page()

with gr.Blocks(
    title="Pixal3D | AI Image-to-3D",
    css="footer {display:none !important;} .gradio-container {padding:0 !important; max-width:100% !important; height:100vh !important; overflow:hidden !important;} #proxy-frame {height:100%; max-height:100vh; padding:0; overflow:hidden;}",
    theme=gr.themes.Base(),
) as demo:
    gr.HTML(page_html, elem_id="proxy-frame", js_on_load=page_script if page_script else None)

if __name__ == "__main__":
    demo.launch(share=True)
