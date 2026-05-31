# Minimal Unsloth Gemma 4 GGUF Chat

This folder keeps Unsloth's own environment setup path, then skips the full
Unsloth Studio application and opens llama.cpp's chat UI directly with the model
already loaded.

Default model:

```text
unsloth/gemma-4-E4B-it-GGUF:UD-Q4_K_XL
```

## Colab usage

### Option A: upload only the notebook

Download `Unsloth_Gemma_Chat_Colab.ipynb`, upload it to Google Drive / Colab, choose a GPU runtime, then run all cells. The notebook is self-contained: it clones upstream Unsloth, runs setup, writes the launcher into `/content`, and opens chat.

### Option B: run from this repo/folder

If the repo or this folder is already available in the runtime, run:

```bash
bash unsloth_gemma_chat/setup_and_launch.sh
```

The shell script will:

1. Clone `https://github.com/unslothai/unsloth.git` into `/content/unsloth`.
2. Run Unsloth's upstream `studio/setup.sh --local` with chat-only flags:
   `UNSLOTH_STUDIO_LLAMA_ONLY=1` and `SKIP_STUDIO_FRONTEND=1`.
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
