#!/usr/bin/env bash
# Start a new film from the starter template:   engine/new_story.sh <film_folder>
# Creates <film_folder>/story/ (script_data.py + project.py to edit) and prints the command that makes the film.
set -euo pipefail
[ $# -ge 1 ] || { echo "usage: $0 <film_folder>"; exit 1; }
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FILM="$1"
if [ -e "$FILM/story" ]; then echo "$FILM/story already exists — not overwriting."; exit 1; fi
mkdir -p "$FILM"
cp -R "$ROOT/templates/story" "$FILM/story"
FILM="$(cd "$FILM" && pwd)"
cat <<EOF
New film started: $FILM
  1. Edit $FILM/story/script_data.py   (scenes, Khmer lines, cameras — see $ROOT/references/screenplay-format.md)
  2. Edit $FILM/story/project.py       (title, chapters, voice descriptions)
  3. Make it:  $ROOT/engine/run_all.sh "$FILM/story" "$FILM"
EOF
