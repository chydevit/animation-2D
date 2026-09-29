# Production workflow

## Environments
- **Drawing / audio mix** (`ANIM`): Python 3.12 with `skia-python numpy scipy soundfile` (`requirements-anim.txt`).
- **Voices / Khmer text** (`VOX`): Python 3.12 with `voxcpm soundfile librosa torch Pillow` (`requirements-voice.txt`).
  Pillow must report `features.check("raqm") == True` (Homebrew Pillow wheels do) for Khmer shaping.
- `ffmpeg` on PATH (H.264 + AAC encoders; no drawtext needed).
- The VoxCPM2 model (`openbmb/VoxCPM2`) downloads to `~/.cache/huggingface` on first use (~5 GB).

## Pipeline (what `engine/run_all.sh` does)
| Step | Script | Output (inside the episode folder) |
|---|---|---|
| voice design: 2 candidates per speaker from a text description | `voice_design.py` (VOX) | `audio/voices/candidates/` + `stats.json` (pitch, stability, voicing) |
| lock one voice per speaker | `lock_voices.py` (VOX) | `audio/voices/<id>.wav/.txt`, `voice_lock.json` |
| title + chapter cards | `make_cards.py` (VOX) | `characters/cards/*.png` |
| voice every line (clone from the locked reference, QA per line, retries) | `tts_loop.sh` → `tts_all.py` | `audio/dialogue/Lnnn_<id>.wav`, `manifest.json` |
| character sheets | `sheet.py all` | `characters/*_sheet.png`, `00_lineup.png` |
| storyboard | `render.py board` | `visuals/storyboard/shot_nnn.jpg` |
| render | `render.py shots [ids]` | `visuals/shots/shot_nnn.mp4` (1920×1080, 24 fps, H.264) |
| mix | `mix.py audio` | `audio/mix.wav`, stems, `audio/music/`, `audio/sfx/` |
| docs | `mix.py docs` | `subtitles_kh.srt`, `subtitles_en.srt`, `docs/scenes.json`, screenplays |
| assemble | `mix.py assemble` | `<OUT_MP4>` with AAC 48 kHz stereo, loudness-normalised, 2 subtitle tracks |
| bible / continuity / QA | `docs.py bible continuity`, `qa.py` | `docs/character_bible.json`, `docs/continuity_report.txt`, `docs/qa_report.txt` |

Timing comes from the real audio: each dialogue shot lasts lead + line + pause, so **render only after TTS**.
Shots of scenes whose lines are all voiced can be rendered early — later scenes never move earlier ones.

## Lessons learned (read before running)
- **Memory.** VoxCPM2 must run in float32 on Apple Silicon (bf16/fp16 glitch); that is ~9 GB. Close heavy apps.
  The MPS cache grows per line: `tts_loop.sh` restarts the process every `TTS_BATCH` (default 8) lines and
  `tts_all.py` empties the cache after each line. With this, a line takes ~10–30 s; without it, minutes.
- **Never run two model processes at once** (e.g. voice design and TTS) — two float32 copies thrash the machine.
  To stop the loop, kill `tts_loop.sh` *and* the Python child (it shows up under the Homebrew Python path).
- **Silent kills** during model load (no traceback, only a `resource_tracker` warning) mean out of memory.
- **Voice design QA**: reject candidates with a pitch outside the role's range (a male role at 300+ Hz), a voiced
  ratio below ~0.55 (whisper/silence) or a very unstable pitch. Redesign with a clearer description, or reuse an
  installed voice from another project via `project.REUSE` / `REUSE_LOCK`.
- **Line QA** flags very short single words (e.g. a whispered name) — check them by ear; they are usually fine.
- **Paths**: every script writes only inside `EPISODE_DIR`; do not copy a pipeline between projects without
  checking where it writes.
- **Speakers who exit** do so after their line (the planner delays `exit_*` for the speaker).
- **Facing**: characters face whoever speaks; task poses (`write`, `work`, `hoe`, `sweep`, `stir`, `cyclo`, `bed`)
  keep the scene's start facing.

## Review checklist (per scene)
Faces/hair/costume from the locked spec · correct costume variant for the story point · voice id per speaker ·
lip-sync on on-screen speakers (inner-voice lines have no lip movement) · location + time of day · period props, no
modern objects · no extra/missing limbs · subtitle text = spoken text · no unwanted text · no watermark ·
consistent with the source.

## Fixing things
- One line sounds wrong → edit its `tts=` text, delete that line from `audio/dialogue/manifest.json`, re-run
  `tts_loop.sh`; then re-render only the shots of that scene and `mix.py audio assemble`.
- One shot looks wrong → fix, `render.py shots <id>`, `mix.py assemble` (audio unchanged if timing unchanged).
- Frame-count check after partial re-renders: every `visuals/shots/shot_nnn.mp4` must have exactly
  `round(t1*24) - round(t0*24)` frames (see `qa.py`).
