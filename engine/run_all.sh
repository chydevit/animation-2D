#!/bin/zsh
# Make (or resume) a whole film:   engine/run_all.sh <story_dir> <episode_dir>
#   <story_dir>   contains script_data.py (screenplay) and project.py (titles, voices, notes)
#   <episode_dir> receives everything: audio/, visuals/, characters/, docs/, subtitles and the MP4
# Every step skips work that is already done, so re-running after a crash or an edit is cheap.
set -e
if [ $# -lt 2 ]; then echo "usage: $0 <story_dir> <episode_dir>"; exit 1; fi
ENGINE="$(cd "$(dirname "$0")" && pwd)"
export STORY_DIR="$(cd "$1" && pwd)"
mkdir -p "$2"; export EPISODE_DIR="$(cd "$2" && pwd)"
VOX=${VOX:-$HOME/voxcpm-env/bin/python}     # VoxCPM2 environment (Python 3.12, torch, voxcpm, Pillow+raqm)
ANIM=${ANIM:-$HOME/anim-env/bin/python}     # drawing environment (skia-python, numpy, scipy, soundfile)
cd "$ENGINE"
if [ ! -f "$EPISODE_DIR/audio/voices/voice_lock.json" ]; then
  echo "== voices: design candidates + lock one voice per character"
  $VOX voice_design.py && $VOX lock_voices.py
fi
echo "== title + chapter cards";               $VOX make_cards.py
echo "== Khmer voice lines (batched TTS)";      VOX=$VOX ./tts_loop.sh
echo "== character sheets";                     $ANIM sheet.py all >/dev/null
echo "== storyboard (one frame per shot)";      $ANIM render.py board >/dev/null
echo "== 2D render";                            JOBS=${JOBS:-5} $ANIM render.py shots
echo "== audio mix, subtitles, docs, MP4";      $ANIM mix.py audio docs assemble
echo "== bible, continuity, QA";                $ANIM docs.py bible continuity && $ANIM qa.py
