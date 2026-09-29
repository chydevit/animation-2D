#!/usr/bin/env bash
# One-step installer for create-animation-2d (Khmer-first 2D animated films + Claude Code skill).
#
#   curl -fsSL https://raw.githubusercontent.com/chydevit/animation-2D/main/install.sh | bash
#
# Options (pass after `bash -s --` when piping, e.g. `| bash -s -- --skill-only`):
#   --skill-only      only install/update the Claude Code skill (no Python environments)
#   --dir PATH        where to put the skill (default: ~/.claude/skills/create-animation-2d)
#   --no-voice        skip the VoxCPM2 voice environment (drawing only)
# Safe to re-run: existing environments are kept, the skill is updated with `git pull`.
set -euo pipefail

REPO="https://github.com/chydevit/animation-2D.git"
DEST="$HOME/.claude/skills/create-animation-2d"
ANIM="$HOME/anim-env"
VOX="$HOME/voxcpm-env"
SKILL_ONLY=0; NO_VOICE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --skill-only) SKILL_ONLY=1 ;;
    --no-voice) NO_VOICE=1 ;;
    --dir) DEST="$2"; shift ;;
    -h|--help) sed -n '2,12p' "$0" 2>/dev/null || true; exit 0 ;;
    *) echo "unknown option: $1"; exit 1 ;;
  esac
  shift
done

say()  { printf '\033[1;32m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!\033[0m %s\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }

# ── 1. the skill ───────────────────────────────────────────────────────────────────────────────
have git || { warn "git is required (macOS: xcode-select --install)"; exit 1; }
if [ -d "$DEST/.git" ]; then
  say "Updating the skill in $DEST"
  git -C "$DEST" pull --ff-only
elif [ -e "$DEST" ]; then
  warn "$DEST already exists and is not a git checkout — leaving it untouched."
  warn "Remove it or pass --dir to install elsewhere."; exit 1
else
  say "Installing the skill into $DEST"
  mkdir -p "$(dirname "$DEST")"
  git clone --depth 1 "$REPO" "$DEST"
fi
chmod +x "$DEST"/engine/*.sh "$DEST"/install.sh 2>/dev/null || true
[ "$SKILL_ONLY" = 1 ] && { say "Done (skill only). Claude Code will pick up 'create-animation-2d' in new sessions."; exit 0; }

# ── 2. system tools ────────────────────────────────────────────────────────────────────────────
OS="$(uname -s)"
PY=""
for c in python3.12 /opt/homebrew/bin/python3.12 /usr/local/bin/python3.12; do
  if have "$c" || [ -x "$c" ]; then PY="$c"; break; fi
done
if [ "$OS" = "Darwin" ] && have brew; then
  [ -n "$PY" ] || { say "Installing Python 3.12 (Homebrew)"; brew install python@3.12; PY="$(brew --prefix)/bin/python3.12"; }
  have ffmpeg || { say "Installing ffmpeg (Homebrew)"; brew install ffmpeg; }
fi
[ -n "$PY" ] || { warn "Python 3.12 is required (macOS: brew install python@3.12; Linux: your package manager)"; exit 1; }
have ffmpeg || { warn "ffmpeg is required (macOS: brew install ffmpeg; Linux: apt install ffmpeg)"; exit 1; }

# ── 3. Python environments (kept if they already work) ─────────────────────────────────────────
if "$ANIM/bin/python" -c "import skia, numpy, scipy, soundfile" 2>/dev/null; then
  say "Drawing environment OK: $ANIM"
else
  say "Creating the drawing environment: $ANIM"
  "$PY" -m venv "$ANIM"
  "$ANIM/bin/pip" install -q --upgrade pip
  "$ANIM/bin/pip" install -q -r "$DEST/requirements-anim.txt"
fi

if [ "$NO_VOICE" = 1 ]; then
  warn "Skipping the voice environment (--no-voice): run_all.sh needs it for voices and Khmer title cards."
elif "$VOX/bin/python" -c "import voxcpm, soundfile, librosa, PIL" 2>/dev/null; then
  say "Voice environment OK: $VOX"
else
  say "Creating the voice environment: $VOX  (VoxCPM2; the ~5 GB model downloads on first use)"
  "$PY" -m venv "$VOX"
  "$VOX/bin/pip" install -q --upgrade pip
  "$VOX/bin/pip" install -q -r "$DEST/requirements-voice.txt"
fi

# ── 4. checks ──────────────────────────────────────────────────────────────────────────────────
if [ "$NO_VOICE" = 0 ]; then
  if "$VOX/bin/python" -c "from PIL import features; import sys; sys.exit(0 if features.check('raqm') else 1)" 2>/dev/null; then
    say "Khmer text shaping (libraqm) OK"
  else
    warn "Pillow in $VOX has no libraqm: Khmer title cards will render incorrectly."
    warn "Fix (macOS): brew install libraqm && $VOX/bin/pip install --force-reinstall --no-binary Pillow Pillow"
  fi
fi

cat <<EOF

$(say "Installed.")
  Skill:        $DEST   (Claude Code: ask for a Khmer 2D cartoon / animated adaptation)
  Try it:       $DEST/engine/run_all.sh $DEST/templates/story ~/animation-2d-films/starter
  New film:     $DEST/engine/new_story.sh ~/animation-2d-films/my-film
  Docs:         $DEST/README.md · references/workflow.md · references/screenplay-format.md
Tip: close memory-heavy apps before voicing — VoxCPM2 needs ~9 GB of RAM on Apple Silicon.
EOF
