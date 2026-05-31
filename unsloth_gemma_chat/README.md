# Minimal Unsloth Gemma 4 GGUF Chat

This folder uses Unsloth's own `studio/install_llama_prebuilt.py` llama.cpp
installer, skips the full Unsloth Studio application, and opens a custom chat UI
with the model already loaded. The custom UI includes Thinking, Web Search
Auto/On/Off, and Code Mode toggles.

Default model:

```text
unsloth/gemma-4-E4B-it-GGUF:UD-Q4_K_XL
```

## Colab usage

### Option A: upload only the notebook

Download `Unsloth_Gemma_Chat_Colab.ipynb`, upload it to Google Drive / Colab, choose a GPU runtime, then run all cells. The notebook is self-contained: it clones upstream Unsloth, installs llama.cpp, writes the launcher into `/content`, and opens chat.

### Option B: run from this repo/folder

If the repo or this folder is already available in the runtime, run:

```bash
bash unsloth_gemma_chat/setup_and_launch.sh
```

The shell script will:

1. Clone `https://github.com/unslothai/unsloth.git` into `/content/unsloth`.
2. Install a prebuilt `llama-server` via Unsloth's upstream `studio/install_llama_prebuilt.py`.
3. Start the installed `llama-server` with `-hf unsloth/gemma-4-E4B-it-GGUF:UD-Q4_K_XL`.
4. Render the ready-to-chat llama.cpp UI in Colab through the Colab port proxy.

## Useful overrides

```bash
# Pick another quant or model reference supported by llama-server -hf.
export UNSLOTH_CHAT_MODEL="unsloth/gemma-4-E4B-it-GGUF:UD-Q4_K_XL"

# Change context length, port, or extra llama-server flags.
export UNSLOTH_CHAT_CTX=4096
export UNSLOTH_CHAT_PORT=8888
export UNSLOTH_CHAT_EXTRA_ARGS="--temp 1.0 --top-p 0.95"

bash unsloth_gemma_chat/setup_and_launch.sh
```

Set `UNSLOTH_CHAT_GPU=off` to avoid adding GPU offload flags even when a GPU tool
is detected.
