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
