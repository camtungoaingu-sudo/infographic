# Emotion Infographic Studio for Codex

This repository is ready to upload to GitHub and connect to Codex Web.

## What is included

- `.agents/plugins/marketplace.json`: Codex plugin marketplace entry.
- `plugins/emotion-infographic-studio/.codex-plugin/plugin.json`: plugin manifest.
- `plugins/emotion-infographic-studio/skills/emotion-infographic-studio/SKILL.md`: orchestration skill.
- `plugins/emotion-infographic-studio/scripts/`: storyboard PNG renderer.
- `requirements.txt`: Python dependency for the renderer.
- `setup_codex.sh`: setup script for Codex Web environments.

## Codex Web setup

In the Codex Web environment for this repo, use this manual setup script:

```bash
bash setup_codex.sh
```

Or paste these commands directly:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install --with-deps chromium
```

After setup succeeds, create a new Codex task and ask:

```text
Use $emotion-infographic-studio with this product image.
```

## Expected workflow

When triggered with a product image, the plugin skill instructs Codex to:

1. Write full product and campaign context.
2. Plan four 15-second ad scenes with camera and audio.
3. Write and coordinate eight start/end frame prompts.
4. Render a storyboard infographic PNG.
5. Write a final video generation prompt.

If image generation is unavailable in the current Codex environment, the skill still writes frame prompts and renders the infographic with product image placeholders.

## Minimal Unsloth Gemma 4 chat launcher

This repo also includes a chat-only launcher in `unsloth_gemma_chat/`. It uses
Unsloth's upstream `studio/install_llama_prebuilt.py` llama.cpp installer instead
of the full Studio setup path, then starts `llama-server` with
`unsloth/gemma-4-E4B-it-GGUF:UD-Q4_K_XL` and opens the ready chat UI directly.
The included UI adds Thinking, Web Search Auto/On/Off, and Code Mode toggles.

For the easiest Colab flow, download `unsloth_gemma_chat/Unsloth_Gemma_Chat_Colab.ipynb`, upload that single notebook to Google Drive / Colab, select a GPU runtime, and run cells one-by-one. The notebook is self-contained, split into debug-friendly steps, and writes the launcher into `/content` automatically.

If this repository/folder is already present in the runtime, you can also run:

```bash
bash unsloth_gemma_chat/setup_and_launch.sh
```

Useful knobs:

```bash
export UNSLOTH_CHAT_MODEL="unsloth/gemma-4-E4B-it-GGUF:UD-Q4_K_XL"
export UNSLOTH_CHAT_CTX=4096
export UNSLOTH_CHAT_PORT=8888
export UNSLOTH_CHAT_EXTRA_ARGS="--temp 1.0 --top-p 0.95"
bash unsloth_gemma_chat/setup_and_launch.sh
```
