#!/usr/bin/env python3
"""Launch a preloaded Unsloth Gemma 4 GGUF chat UI with llama-server.

The environment preparation stays in Unsloth's upstream llama.cpp installer.
This launcher starts the installed ``llama-server`` on an internal port, then
serves a small chat UI with Thinking, Web Search, and Code Mode controls.
"""

from __future__ import annotations

import html
import importlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import signal
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

DEFAULT_MODEL_REF = "unsloth/gemma-4-E4B-it-GGUF:UD-Q4_K_XL"
DEFAULT_PORT = 8888
DEFAULT_INTERNAL_PORT_OFFSET = 1


WEB_SEARCH_TRIGGERS = (
    "today",
    "latest",
    "current",
    "news",
    "price",
    "weather",
    "schedule",
    "version",
    "release",
    "update",
    "now",
    "2025",
    "2026",
    "hôm nay",
    "mới nhất",
    "hiện tại",
    "tin tức",
    "giá",
    "thời tiết",
    "lịch",
    "phiên bản",
)


HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Unsloth Gemma 4 Chat</title>
<style>
:root { color-scheme: dark; --bg:#080808; --panel:#151515; --muted:#aaa; --line:#333; --accent:#76d191; }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:#f5f5f5; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
.app { height:100vh; display:flex; flex-direction:column; }
.header { display:flex; align-items:center; gap:12px; padding:12px 18px; border-bottom:1px solid var(--line); background:#050505; }
.logo { font-size:18px; font-weight:800; }
.model { margin-left:auto; padding:6px 10px; border-radius:10px; background:#242424; color:#e8e8e8; font-size:12px; border:1px solid #3a3a3a; }
.messages { flex:1; overflow:auto; padding:22px max(16px, calc((100vw - 980px)/2)); }
.msg { display:flex; margin:16px 0; }
.bubble { max-width:min(860px, 92vw); white-space:pre-wrap; line-height:1.5; padding:14px 16px; border-radius:18px; border:1px solid var(--line); }
.user { justify-content:flex-end; }
.user .bubble { background:#2a2a2a; }
.assistant .bubble { background:#111; }
.meta { color:var(--muted); font-size:12px; margin-top:8px; }
.composer { margin:0 auto 18px; width:min(920px, calc(100vw - 28px)); border:1px solid #555; border-radius:24px; background:#1b1b1b; padding:12px; }
textarea { width:100%; min-height:74px; resize:vertical; background:transparent; color:#fff; border:0; outline:0; font:16px/1.4 inherit; }
.toolbar { display:flex; align-items:center; gap:8px; flex-wrap:wrap; padding-top:8px; }
button { border:1px solid #444; background:#2b2b2b; color:#e8e8e8; border-radius:999px; padding:8px 12px; cursor:pointer; font-weight:700; }
button:hover { border-color:#777; }
button.on { background:#173821; border-color:#3a9d59; color:#a7f3bf; }
button.warn { background:#3a2d12; border-color:#a87b22; color:#ffe2a3; }
.send { margin-left:auto; background:#eee; color:#111; border-color:#eee; }
.stop { border-radius:50%; width:38px; height:38px; padding:0; }
.hint { color:var(--muted); font-size:12px; padding:0 2px 4px; }
.error { color:#ffb4b4; }
a { color:#8bd5ff; }
</style>
</head>
<body>
<div class="app">
  <div class="header">
    <div class="logo">🦥 Unsloth Gemma 4 Chat</div>
    <div class="model" id="model"></div>
  </div>
  <div class="messages" id="messages"></div>
  <div class="composer">
    <div class="hint">Shift+Enter xuống dòng • Enter gửi • Web Auto tự tìm khi câu hỏi cần dữ liệu mới</div>
    <textarea id="input" placeholder="Type a message..."></textarea>
    <div class="toolbar">
      <button id="thinking" class="on" title="Bật/tắt hướng dẫn reasoning. Không ép model lộ chain-of-thought ẩn.">Thinking: On</button>
      <button id="web" class="warn" title="Auto: chỉ tìm khi câu hỏi cần thông tin mới. On: luôn tìm. Off: không tìm.">Web: Auto</button>
      <button id="code" title="Bật/tắt chế độ trả lời tối ưu cho code.">Code: Off</button>
      <button class="send" id="send">Send</button>
    </div>
  </div>
</div>
<script>
const MODEL = __MODEL_JSON__;
const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('input');
document.getElementById('model').textContent = MODEL;
let messages = [];
let thinking = true;
let web = 'auto';
let code = false;
let busy = false;
function add(role, text, meta='') {
  const row = document.createElement('div'); row.className = 'msg ' + role;
  const bubble = document.createElement('div'); bubble.className = 'bubble';
  bubble.textContent = text;
  if (meta) { const m = document.createElement('div'); m.className='meta'; m.textContent=meta; bubble.appendChild(m); }
  row.appendChild(bubble); messagesEl.appendChild(row); messagesEl.scrollTop = messagesEl.scrollHeight;
  return bubble;
}
function syncButtons() {
  const t = document.getElementById('thinking'); t.textContent = 'Thinking: ' + (thinking ? 'On' : 'Off'); t.className = thinking ? 'on' : '';
  const w = document.getElementById('web'); w.textContent = 'Web: ' + (web === 'auto' ? 'Auto' : (web === 'on' ? 'On' : 'Off')); w.className = web === 'off' ? '' : (web === 'auto' ? 'warn' : 'on');
  const c = document.getElementById('code'); c.textContent = 'Code: ' + (code ? 'On' : 'Off'); c.className = code ? 'on' : '';
}
document.getElementById('thinking').onclick = () => { thinking = !thinking; syncButtons(); };
document.getElementById('web').onclick = () => { web = web === 'auto' ? 'on' : (web === 'on' ? 'off' : 'auto'); syncButtons(); };
document.getElementById('code').onclick = () => { code = !code; syncButtons(); };
async function send() {
  if (busy) return;
  const text = inputEl.value.trim(); if (!text) return;
  inputEl.value = ''; busy = true;
  messages.push({role:'user', content:text}); add('user', text);
  const pending = add('assistant', 'Thinking...');
  try {
    const res = await fetch('/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({messages, thinking, web, code})});
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Request failed');
    pending.textContent = data.answer || '';
    if (data.web_used) {
      const meta = document.createElement('div'); meta.className = 'meta'; meta.textContent = 'Web search used' + (data.sources?.length ? ': ' + data.sources.map(s => s.title).join(' • ') : ''); pending.appendChild(meta);
    }
    messages.push({role:'assistant', content:data.answer || ''});
  } catch (err) {
    pending.textContent = 'Error: ' + err.message; pending.classList.add('error');
  } finally { busy = false; messagesEl.scrollTop = messagesEl.scrollHeight; }
}
document.getElementById('send').onclick = send;
inputEl.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }});
syncButtons();
add('assistant', 'Ready. Model is preloaded. Use Thinking / Web / Code toggles below.');
</script>
</body>
</html>
"""


def _has_gpu_tool() -> bool:
    gpu_tools = ("nvidia-smi", "rocminfo", "amd-smi", "hipconfig", "hipinfo")
    return any(shutil.which(name) for name in gpu_tools)


def _find_llama_server() -> str:
    explicit = os.getenv("LLAMA_SERVER_PATH")
    if explicit:
        path = Path(explicit).expanduser()
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
        raise FileNotFoundError(f"LLAMA_SERVER_PATH is not executable: {path}")

    candidates = [
        Path.home() / ".unsloth" / "llama.cpp" / "build" / "bin" / "llama-server",
        Path.home() / ".unsloth" / "llama.cpp" / "llama-server",
        Path.home() / ".unsloth" / "studio" / "llama.cpp" / "build" / "bin" / "llama-server",
        Path.home() / ".unsloth" / "studio" / "llama.cpp" / "llama-server",
    ]
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)

    on_path = shutil.which("llama-server")
    if on_path:
        return on_path

    searched = "\n".join(f"  - {p}" for p in candidates)
    raise FileNotFoundError(
        "Could not find llama-server. Run unsloth_gemma_chat/setup_and_launch.sh first "
        "or set LLAMA_SERVER_PATH. Searched:\n" + searched
    )


def _port_is_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _wait_for_server(
    port: int, process: subprocess.Popen[str], timeout_s: int = 1800
) -> None:
    deadline = time.monotonic() + timeout_s
    last_status = 0.0
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"llama-server exited early with code {process.returncode}")
        if _port_is_open(port):
            for endpoint in ("/health", "/v1/models", "/"):
                try:
                    with urllib.request.urlopen(
                        f"http://127.0.0.1:{port}{endpoint}", timeout=2
                    ):
                        return
                except urllib.error.HTTPError as exc:
                    if exc.code < 500:
                        return
                except Exception:
                    pass
        now = time.monotonic()
        if now - last_status > 15:
            print("Waiting for Gemma 4 GGUF to load...", flush=True)
            last_status = now
        time.sleep(1)
    raise TimeoutError(f"llama-server did not become ready within {timeout_s} seconds")


def _colab_proxy_url(port: int) -> str:
    fallback = f"http://127.0.0.1:{port}"
    if importlib.util.find_spec("google.colab.output") is None:
        return fallback

    colab_output = importlib.import_module("google.colab.output")
    for _ in range(3):
        try:
            url = colab_output.eval_js(
                f"google.colab.kernel.proxyPort({port})", timeout_sec=10
            )
            if isinstance(url, str) and url.startswith("https://"):
                return url.rstrip("/")
        except Exception:
            time.sleep(1)
    return fallback


def _display_chat(port: int) -> None:
    url = _colab_proxy_url(port)
    print(f"\nUnsloth Gemma chat is ready: {url}\n", flush=True)
    if importlib.util.find_spec("IPython.display") is None:
        return

    display_mod = importlib.import_module("IPython.display")
    display_mod.display(
        display_mod.HTML(f"""
<div style="font-family:system-ui,-apple-system,sans-serif;margin:8px 0;border-radius:12px;overflow:hidden;box-shadow:0 2px 16px rgba(0,0,0,.18);">
  <div style="display:flex;align-items:center;gap:10px;padding:10px 16px;background:#000;color:#fff;">
    <strong>Unsloth Gemma 4 Chat</strong>
    <a href="{html.escape(url)}" target="_blank" style="margin-left:auto;color:#9ae6b4;text-decoration:none;font-weight:700;">Open in new tab</a>
  </div>
  <iframe src="{html.escape(url)}" style="width:100%;height:82vh;min-height:620px;border:0;display:block;" allow="clipboard-read; clipboard-write"></iframe>
</div>
""")
    )


def _build_command(binary: str, port: int, model_ref: str) -> list[str]:
    host = os.getenv("UNSLOTH_LLAMA_HOST", "127.0.0.1")
    ctx_size = os.getenv("UNSLOTH_CHAT_CTX", "4096")
    parallel = os.getenv("UNSLOTH_CHAT_PARALLEL", "1")

    cmd = [
        binary,
        "-hf",
        model_ref,
        "--host",
        host,
        "--port",
        str(port),
        "-c",
        ctx_size,
        "--parallel",
        parallel,
        "--threads",
        os.getenv("UNSLOTH_CHAT_THREADS", "-1"),
        "--jinja",
        "--flash-attn",
        "on",
    ]

    if os.getenv("UNSLOTH_CHAT_GPU", "auto").lower() != "off" and _has_gpu_tool():
        cmd.extend(["-ngl", "-1"])

    extra = os.getenv("UNSLOTH_CHAT_EXTRA_ARGS", "").strip()
    if extra:
        cmd.extend(shlex.split(extra))
    return cmd


def _should_search_web(mode: str, messages: list[dict[str, str]]) -> bool:
    if mode == "on":
        return True
    if mode == "off":
        return False
    last = messages[-1]["content"].lower() if messages else ""
    return any(trigger in last for trigger in WEB_SEARCH_TRIGGERS)


def _search_web(query: str, limit: int = 4) -> list[dict[str, str]]:
    encoded = urllib.parse.urlencode({"q": query})
    url = f"https://duckduckgo.com/html/?{encoded}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 UnslothGemmaChat/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            body = response.read().decode("utf-8", errors="ignore")
    except Exception as exc:
        return [{"title": "Web search failed", "url": "", "snippet": str(exc)}]

    results: list[dict[str, str]] = []
    pattern = re.compile(
        r'<a rel="nofollow" class="result__a" href="(?P<url>[^"]+)".*?>(?P<title>.*?)</a>.*?'
        r'<a class="result__snippet".*?>(?P<snippet>.*?)</a>',
        re.DOTALL,
    )
    for match in pattern.finditer(body):
        title = re.sub(r"<.*?>", "", match.group("title"))
        snippet = re.sub(r"<.*?>", "", match.group("snippet"))
        result_url = urllib.parse.unquote(html.unescape(match.group("url")))
        if "uddg=" in result_url:
            parsed = urllib.parse.urlparse(result_url)
            qs = urllib.parse.parse_qs(parsed.query)
            result_url = qs.get("uddg", [result_url])[0]
        results.append(
            {
                "title": html.unescape(title).strip(),
                "url": result_url,
                "snippet": html.unescape(snippet).strip(),
            }
        )
        if len(results) >= limit:
            break
    return results


def _system_messages(
    *, thinking: bool, code: bool, web_used: bool, sources: list[dict[str, str]]
) -> list[dict[str, str]]:
    prompts = [
        "You are Unsloth Gemma 4 running locally via llama-server. Answer clearly.",
    ]
    if thinking:
        prompts.append(
            "Thinking mode is ON: reason carefully before answering, but do not reveal hidden chain-of-thought. Provide a short reasoning summary only when useful."
        )
    else:
        prompts.append(
            "Thinking mode is OFF: answer directly and do not include reasoning traces or chain-of-thought."
        )
    if code:
        prompts.append(
            "Code mode is ON: prioritize correct runnable code, explain file/command steps, include edge cases, and use Markdown code fences."
        )
    if web_used and sources:
        formatted_sources = []
        for idx, source in enumerate(sources, start=1):
            formatted_sources.append(
                f"[{idx}] {source.get('title', '')}\nURL: {source.get('url', '')}\nSnippet: {source.get('snippet', '')}"
            )
        prompts.append(
            "Web search context is available. Use it only when relevant and cite sources by bracket number.\n"
            + "\n\n".join(formatted_sources)
        )
    return [{"role": "system", "content": "\n\n".join(prompts)}]


def _call_llama_server(
    *, api_port: int, model_ref: str, messages: list[dict[str, str]]
) -> str:
    payload = {
        "model": model_ref,
        "messages": messages,
        "stream": False,
        "temperature": float(os.getenv("UNSLOTH_CHAT_TEMPERATURE", "0.7")),
        "max_tokens": int(os.getenv("UNSLOTH_CHAT_MAX_TOKENS", "2048")),
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:{api_port}/v1/chat/completions",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        result = json.loads(response.read().decode("utf-8"))
    return result["choices"][0]["message"].get("content", "")


def _make_ui_handler(api_port: int, model_ref: str) -> type[BaseHTTPRequestHandler]:
    page = HTML_PAGE.replace("__MODEL_JSON__", json.dumps(model_ref))

    class ChatHandler(BaseHTTPRequestHandler):
        server_version = "UnslothGemmaChat/1.0"

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _write_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path not in ("/", "/index.html"):
                self.send_error(404)
                return
            body = page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            if self.path != "/api/chat":
                self.send_error(404)
                return
            length = int(self.headers.get("Content-Length", "0"))
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                messages = payload.get("messages") or []
                thinking = bool(payload.get("thinking", True))
                web_mode = str(payload.get("web", "auto"))
                code = bool(payload.get("code", False))
                if not messages or not isinstance(messages, list):
                    raise ValueError("messages must be a non-empty list")
                web_used = _should_search_web(web_mode, messages)
                sources = _search_web(messages[-1]["content"]) if web_used else []
                full_messages = _system_messages(
                    thinking=thinking, code=code, web_used=web_used, sources=sources
                ) + messages
                answer = _call_llama_server(
                    api_port=api_port, model_ref=model_ref, messages=full_messages
                )
                self._write_json(
                    200, {"answer": answer, "web_used": web_used, "sources": sources}
                )
            except Exception as exc:
                self._write_json(500, {"error": str(exc)})

    return ChatHandler


def _start_ui_server(port: int, api_port: int, model_ref: str) -> ThreadingHTTPServer:
    handler = _make_ui_handler(api_port, model_ref)
    server = ThreadingHTTPServer(("0.0.0.0", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def main() -> int:
    model_ref = os.getenv("UNSLOTH_CHAT_MODEL", DEFAULT_MODEL_REF)
    ui_port = int(os.getenv("UNSLOTH_CHAT_PORT", str(DEFAULT_PORT)))
    api_port = int(
        os.getenv(
            "UNSLOTH_LLAMA_SERVER_PORT",
            str(ui_port + DEFAULT_INTERNAL_PORT_OFFSET),
        )
    )
    timeout_s = int(os.getenv("UNSLOTH_CHAT_LOAD_TIMEOUT", "1800"))
    binary = _find_llama_server()

    cmd = _build_command(binary, api_port, model_ref)
    print("Starting preloaded chat model:", model_ref, flush=True)
    print("Command:", " ".join(shlex.quote(part) for part in cmd), flush=True)

    process = subprocess.Popen(cmd, text=True)
    ui_server: ThreadingHTTPServer | None = None

    def _stop(_signum: int | None = None, _frame: object | None = None) -> None:
        if ui_server is not None:
            ui_server.shutdown()
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()
        raise SystemExit(0)

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    _wait_for_server(api_port, process, timeout_s=timeout_s)
    ui_server = _start_ui_server(ui_port, api_port, model_ref)
    _display_chat(ui_port)

    print("Keep this cell/process running to keep the chat server alive.", flush=True)
    while process.poll() is None:
        time.sleep(300)
        print("=", end="", flush=True)
    if ui_server is not None:
        ui_server.shutdown()
    return int(process.returncode or 0)


if __name__ == "__main__":
    raise SystemExit(main())
