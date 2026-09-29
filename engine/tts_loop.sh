#!/bin/zsh
# Run tts_all.py in batches (a fresh process every TTS_BATCH lines) until every line is voiced.
# VoxCPM2 on Apple Silicon needs float32 (~9 GB); the MPS cache grows per line, so short batches keep it fast.
cd "$(dirname "$0")"
export TTS_BATCH=${TTS_BATCH:-8}
VOX=${VOX:-$HOME/voxcpm-env/bin/python}
LOG="${EPISODE_DIR:-.}/tts_all.log"
while true; do
  $VOX tts_all.py >> "$LOG" 2>&1
  rc=$?
  if [ $rc -ne 3 ]; then echo "TTS_LOOP_EXIT $rc" >> "$LOG"; exit $rc; fi
done
