#!/usr/bin/env bash
set -euo pipefail

# Minimal Unsloth GGUF chat launcher.
# It intentionally keeps Unsloth's own setup pipeline for Python/llama.cpp, but
# skips the full Studio frontend because this project opens llama-server's chat
# UI directly with the model already loaded.

UNSLOTH_REPO_URL="${UNSLOTH_REPO_URL:-https://github.com/unslothai/unsloth.git}"
UNSLOTH_BRANCH="${UNSLOTH_BRANCH:-main}"
if [ -d /content ]; then
  DEFAULT_UNSLOTH_REPO_DIR="/content/unsloth"
else
  DEFAULT_UNSLOTH_REPO_DIR="$HOME/unsloth"
fi
UNSLOTH_REPO_DIR="${UNSLOTH_REPO_DIR:-$DEFAULT_UNSLOTH_REPO_DIR}"
CHAT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -d "$UNSLOTH_REPO_DIR/.git" ]; then
  echo "Cloning Unsloth into $UNSLOTH_REPO_DIR..."
  git clone --depth 1 --branch "$UNSLOTH_BRANCH" "$UNSLOTH_REPO_URL" "$UNSLOTH_REPO_DIR"
else
  echo "Using existing Unsloth checkout at $UNSLOTH_REPO_DIR"
fi

cd "$UNSLOTH_REPO_DIR"
chmod +x studio/setup.sh

# Keep the Unsloth-maintained environment and llama.cpp installer, but avoid
# rebuilding the entire Studio web application for a chat-only workflow.
export UNSLOTH_STUDIO_LLAMA_ONLY="${UNSLOTH_STUDIO_LLAMA_ONLY:-1}"
export SKIP_STUDIO_FRONTEND="${SKIP_STUDIO_FRONTEND:-1}"
./studio/setup.sh --local

python "$CHAT_DIR/launch_chat.py"
