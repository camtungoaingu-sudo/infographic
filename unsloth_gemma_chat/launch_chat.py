#!/usr/bin/env python3
"""Launch a preloaded Unsloth Gemma 4 GGUF chat UI with llama-server.

The heavy environment preparation stays in Unsloth's upstream ``studio/setup.sh``.
This file only finds the installed ``llama-server``, starts it with the desired
Hugging Face GGUF reference, opens the llama.cpp chat UI, and keeps the process
alive for Colab.
"""

from __future__ import annotations

import os
import shlex
import shutil
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_MODEL_REF = "unsloth/gemma-4-E4B-it-GGUF:UD-Q4_K_XL"
DEFAULT_PORT = 8888


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


def _wait_for_server(port: int, process: subprocess.Popen[str], timeout_s: int = 1800) -> None:
    deadline = time.monotonic() + timeout_s
    last_status = 0.0
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"llama-server exited early with code {process.returncode}")
        if _port_is_open(port):
            for endpoint in ("/health", "/v1/models", "/"):
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}{endpoint}", timeout=2):
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
    try:
        from google.colab.output import eval_js  # type: ignore
    except Exception:
        return fallback

    for _ in range(3):
        try:
            url = eval_js(f"google.colab.kernel.proxyPort({port})", timeout_sec=10)
            if isinstance(url, str) and url.startswith("https://"):
                return url.rstrip("/")
        except Exception:
            time.sleep(1)
    return fallback


def _display_chat(port: int) -> None:
    url = _colab_proxy_url(port)
    print(f"\nUnsloth Gemma chat is ready: {url}\n", flush=True)
    try:
        from IPython.display import HTML, display  # type: ignore
    except Exception:
        return

    display(HTML(f"""
<div style="font-family:system-ui,-apple-system,sans-serif;margin:8px 0;border-radius:12px;overflow:hidden;box-shadow:0 2px 16px rgba(0,0,0,.18);">
  <div style="display:flex;align-items:center;gap:10px;padding:10px 16px;background:#000;color:#fff;">
    <strong>Unsloth Gemma 4 Chat</strong>
    <a href="{url}" target="_blank" style="margin-left:auto;color:#9ae6b4;text-decoration:none;font-weight:700;">Open in new tab</a>
  </div>
  <iframe src="{url}" style="width:100%;height:82vh;min-height:620px;border:0;display:block;" allow="clipboard-read; clipboard-write"></iframe>
</div>
"""))


def _build_command(binary: str, port: int, model_ref: str) -> list[str]:
    host = os.getenv("UNSLOTH_CHAT_HOST", "0.0.0.0")
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


def main() -> int:
    model_ref = os.getenv("UNSLOTH_CHAT_MODEL", DEFAULT_MODEL_REF)
    port = int(os.getenv("UNSLOTH_CHAT_PORT", str(DEFAULT_PORT)))
    timeout_s = int(os.getenv("UNSLOTH_CHAT_LOAD_TIMEOUT", "1800"))
    binary = _find_llama_server()

    cmd = _build_command(binary, port, model_ref)
    print("Starting preloaded chat model:", model_ref, flush=True)
    print("Command:", " ".join(shlex.quote(part) for part in cmd), flush=True)

    process = subprocess.Popen(cmd, text=True)

    def _stop(_signum: int | None = None, _frame: object | None = None) -> None:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()
        raise SystemExit(0)

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    _wait_for_server(port, process, timeout_s=timeout_s)
    _display_chat(port)

    print("Keep this cell/process running to keep the chat server alive.", flush=True)
    while process.poll() is None:
        time.sleep(300)
        print("=", end="", flush=True)
    return int(process.returncode or 0)


if __name__ == "__main__":
    raise SystemExit(main())
