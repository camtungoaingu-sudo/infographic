#!/usr/bin/env bash
set -euo pipefail

# Minimal Unsloth GGUF chat launcher.
# Uses Unsloth's own llama.cpp prebuilt installer, but does not run the full
# Studio setup pipeline because that path installs many training/UI deps and can
# fail in Colab before the chat-only server is needed.

UNSLOTH_REPO_URL="${UNSLOTH_REPO_URL:-https://github.com/unslothai/unsloth.git}"
UNSLOTH_BRANCH="${UNSLOTH_BRANCH:-main}"
if [ -d /content ]; then
  DEFAULT_UNSLOTH_REPO_DIR="/content/unsloth"
else
  DEFAULT_UNSLOTH_REPO_DIR="$HOME/unsloth"
fi
UNSLOTH_REPO_DIR="${UNSLOTH_REPO_DIR:-$DEFAULT_UNSLOTH_REPO_DIR}"
CHAT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LLAMA_CPP_DIR="${LLAMA_CPP_DIR:-$HOME/.unsloth/llama.cpp}"

if [ ! -d "$UNSLOTH_REPO_DIR/.git" ]; then
  echo "Cloning Unsloth into $UNSLOTH_REPO_DIR..."
  git clone --depth 1 --branch "$UNSLOTH_BRANCH" "$UNSLOTH_REPO_URL" "$UNSLOTH_REPO_DIR"
else
  echo "Using existing Unsloth checkout at $UNSLOTH_REPO_DIR"
fi

cd "$UNSLOTH_REPO_DIR"

_pick_prebuilt_repo() {
  if command -v nvidia-smi >/dev/null 2>&1 || command -v rocminfo >/dev/null 2>&1 || \
     command -v amd-smi >/dev/null 2>&1 || command -v hipconfig >/dev/null 2>&1; then
    printf '%s' 'unslothai/llama.cpp'
  else
    printf '%s' 'ggml-org/llama.cpp'
  fi
}

PUBLISHED_REPO="${UNSLOTH_LLAMA_PUBLISHED_REPO:-$(_pick_prebuilt_repo)}"
echo "Installing llama.cpp prebuilt via Unsloth installer ($PUBLISHED_REPO)..."
mkdir -p "$(dirname "$LLAMA_CPP_DIR")"
if ! python studio/install_llama_prebuilt.py \
    --install-dir "$LLAMA_CPP_DIR" \
    --llama-tag "${UNSLOTH_LLAMA_TAG:-latest}" \
    --published-repo "$PUBLISHED_REPO" \
    --simple-policy; then
  if [ "$PUBLISHED_REPO" != "ggml-org/llama.cpp" ]; then
    echo "Primary prebuilt repo failed; retrying ggml-org/llama.cpp..."
    python studio/install_llama_prebuilt.py \
      --install-dir "$LLAMA_CPP_DIR" \
      --llama-tag "${UNSLOTH_LLAMA_TAG:-latest}" \
      --published-repo "ggml-org/llama.cpp" \
      --simple-policy
  else
    exit 1
  fi
fi

python "$CHAT_DIR/launch_chat.py"
