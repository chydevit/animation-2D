# create-animation-2d

**Khmer-first 2D animated films from a story — end to end, on one Mac.**
Screenplay → locked character designs → locked VoxCPM2 voices → lip-synced 2D animation → Cambodian-inspired
music & sound → Khmer/English subtitles → a finished 1080p MP4, with storyboard, character bible and QA report.

Also a [Claude Code](https://claude.com/claude-code) skill (`SKILL.md`) that includes the **Khmer Cartoon Character
Design System** (Khmer boy & girl + 12 supporting characters).

## Install (one step)

**Claude Code skill + everything it needs** (macOS / Linux):
```bash
curl -fsSL https://raw.githubusercontent.com/chydevit/animation-2D/main/install.sh | bash
```
It installs the skill into `~/.claude/skills/create-animation-2d`, creates the two Python environments
(`~/anim-env`, `~/voxcpm-env`), installs ffmpeg/Python 3.12 with Homebrew if missing, and checks Khmer text support.
Re-run it any time to update. Options: `| bash -s -- --skill-only` (skill only) · `--no-voice` · `--dir PATH`.

**Start your own project from this repo:** click **Use this template** at the top of the GitHub page.

**Start a new film:**
```bash
~/.claude/skills/create-animation-2d/engine/new_story.sh ~/animation-2d-films/my-film
```

![cast](docs/images/cast.png)

| | | |
|---|---|---|
| ![](docs/images/shot_014.jpg) | ![](docs/images/shot_083.jpg) | ![](docs/images/shot_161.jpg) |
| ![](docs/images/shot_102.jpg) | ![](docs/images/shot_181.jpg) | ![](docs/images/shot_228.jpg) |

*Frames from the example film ព្រះអាទិត្យថ្មីរះលើផែនដីចាស់ (15 min 49 s), made entirely with this repo.*

## Features
- **2D cut-out character rigs** (vector, skia): walking, pedalling a cyclo, sitting, kneeling, carrying, 20+ gestures,
  10 expressions, 10 mouth shapes, blinking, breathing, speech-driven nods and brow lifts.
- **16 period locations** (late-1950s Cambodia: village, Phnom Penh street, temple, villa, prison, factory, hospital…)
  with parallax, time of day (dawn → night, rain) and lamp lighting; 34 cut-away shots.
- **Voices**: VoxCPM2 voice design → one locked reference voice per character → every line cloned from it, with
  automatic QA and retries. Khmer and English.
- **Lip-sync** from the final audio; per-line loudness matching, clarity EQ and room reverb by location.
- **Procedural audio**: roneat/khloy/skor/ching-inspired music cues, ambiences and 50+ sound effects (no samples).
- **Documents**: Khmer + English screenplays, `scenes.json` (every shot), `character_bible.json`, continuity and
  QA reports, subtitles (SRT + embedded tracks).
- **Content care**: sensitive events are implied only; political material kept neutral.

## Requirements (installed by `install.sh`)
- macOS on Apple Silicon (16 GB RAM; close heavy apps while voicing), or Linux with CUDA for VoxCPM2
- `ffmpeg`
- Two Python 3.12 environments:
  ```bash
  python3.12 -m venv ~/anim-env  && ~/anim-env/bin/pip install -r requirements-anim.txt
  python3.12 -m venv ~/voxcpm-env && ~/voxcpm-env/bin/pip install -r requirements-voice.txt
  ```
  The VoxCPM2 model (~5 GB) downloads on first use.

## Quick start
```bash
# the starter story (two short scenes)
engine/run_all.sh templates/story episodes/starter

# the full example film (~3 h of voicing on an M-series Mac, ~20 min to render)
engine/run_all.sh examples/preah-atit/story episodes/preah-atit
```
Everything is written into the episode folder:
```
episodes/<film>/
  <film>.mp4  subtitles_kh.srt  subtitles_en.srt
  docs/        screenplays, scenes.json, character_bible.json, continuity + QA reports
  characters/  sheets, lineup, title/chapter cards
  audio/       dialogue/ (lines + manifest), voices/ (locked voices), music/, sfx/, mix + stems
  visuals/     storyboard/ (one frame per shot), shots/ (rendered shots)
```
`run_all.sh` is resumable — re-run it after a crash or an edit and it only redoes what is missing.

## Make your own film
1. Copy `templates/story/` and write `script_data.py` (scenes, Khmer lines + English, cameras, poses, moves) and
   `project.py` (titles, chapters, voice descriptions). Format: [`references/screenplay-format.md`](references/screenplay-format.md).
2. Add or adjust characters in `engine/chars.py` (`CAST`) and check them with
   `STORY_DIR=… EPISODE_DIR=… ~/anim-env/bin/python engine/sheet.py <id>`.
3. `engine/run_all.sh <story> <episode>`; review `visuals/storyboard/`; fix and re-render single shots.
Details, lessons learned and troubleshooting: [`references/workflow.md`](references/workflow.md).

## Use as a Claude Code skill
Put (or symlink) this folder in `.claude/skills/create-animation-2d/` (project) or `~/.claude/skills/` (global).
Claude then uses it for Khmer cartoon films, character sheets, Khmer voice lines, and fixes to existing films.

## Notes
- Khmer audio should be reviewed by a Khmer speaker before publishing.
- The example film adapts a publicly available summary of a Khmer novel for education; its dialogue is original.
