---
name: create-animation-2d
description: Make a complete 2D animated film (MP4 + Khmer/English subtitles) from a story, novel summary or script — Khmer-first, with locked character designs, locked VoxCPM2 voices, lip-sync, procedural Cambodian-inspired music/SFX, storyboard, screenplay, scenes.json, character bible and QA. Also the KHMER CARTOON CHARACTER DESIGN SYSTEM (the Khmer boy and girl + 12 supporting characters: sheets, poses, expressions, mouth shapes, image/video prompts). Use whenever the user asks for a Khmer or Cambodian cartoon, a 2D animation or animated adaptation of a story, a character sheet / turnaround / expression sheet, Khmer voice lines, lip-sync, or wants to fix, re-render, re-voice or improve an existing film made with this skill.
---

# Create Animation 2D (Khmer cartoon films)

Everything needed to go from a source story to a playable 2D film, plus the Khmer character design system.
Priority order for every decision: **CHARACTER CONSISTENCY > STORY CONTINUITY > ANIMATION QUALITY > ENVIRONMENT DETAIL.**

## What is in this folder
| Path | Use |
|---|---|
| `engine/` | the film pipeline (rigs, sets, planner, renderer, TTS, audio, mix, docs, QA). Run `engine/run_all.sh <story_dir> <episode_dir>` |
| `examples/preah-atit/story/` | a complete 15-minute film: `script_data.py` (screenplay) + `project.py` (titles, voices, notes) |
| `templates/story/` | starter `script_data.py` + `project.py` for a new film |
| `characters/` | reference sheets of the Khmer boy/girl (`character-sheet.png`) and the supporting cast (`supporting-cast.png`) |
| `references/khmer-character-design.md` | the full character design system (locked designs, poses, expressions, prompt templates) |
| `references/workflow.md` | step-by-step production workflow, lessons learned, troubleshooting |
| `references/screenplay-format.md` | how to write `script_data.py` / `project.py` (items, cameras, moves, poses, locations, inserts) |

## Two modes

### A. Character design only (sheets, prompts, poses)
Read `references/khmer-character-design.md` and look at `characters/character-sheet.png` (and
`characters/supporting-cast.png` for supporting characters) **before** any image, prompt or model. Never redesign a
recurring character. When a tool accepts a reference image, attach the sheet.

### B. A whole film
1. **Read the source completely.** Extract characters, relationships, the order of events and the ending. Adapt; do
   not invent a different story and do not copy long passages.
2. **Write the story folder** (copy `templates/story/`): scenes, dialogue (natural short Khmer; spell numbers out in
   the `tts=` text), English translation, camera/pose/move per item, one start mark per cast member. Put titles,
   chapter names, voice designs and character notes in `project.py`. See `references/screenplay-format.md`.
3. **Design characters** as rig specs in `engine/chars.py` (`CAST`), in the house style: warm tan skin, large
   dark-brown eyes with highlights, dark-brown outlines, soft cel shading. Costume changes only when the story
   requires them — add a variant id (e.g. `sam_prison`) that copies the base spec, and map it to the base voice in
   `VOICE_OF` in `script_data.py`.
4. **Locations**: reuse the sets in `engine/sets.py` (village, street, yard, hut, temple, villa, meyhome, prison,
   visit, newhome, factory, hall, office, clinic, mansion, ward) or add a `Set` subclass. Cut-aways are `insert:<name>`
   cameras implemented in `engine/render.py → draw_insert`.
5. **Run** `engine/run_all.sh <story_dir> <episode_dir>` (resumable). It designs and locks voices, voices every line,
   renders the storyboard and every shot, mixes audio, writes subtitles/docs, assembles the MP4 and runs QA.
6. **Review** before delivering: contact sheets of storyboard frames (`engine/contact.py`) at several points; fix,
   re-render only the affected shots (`render.py shots <ids>`), then `mix.py assemble` again.
7. **Report honestly**: QA output, anything flagged, what a Khmer speaker still needs to check.

## Hard rules
- One locked design per character id; one locked VoxCPM2 reference voice per speaker (`audio/voices/voice_lock.json`).
- Khmer text in images is rendered with Pillow + libraqm (the VoxCPM env has it). Skia cannot shape Khmer.
- No modern objects in historical settings; no text in the picture except title/chapter cards.
- Sensitive events (assault, violence, death, birth, theft) are **implied only**: sound, closed doors, shadows,
  reactions, fades, aftermath. No nudity, blood, injury or technique.
- Political material stays neutral: fictional figures, no parties, slogans, endorsements or modern references.
- Khmer audio must be checked by a Khmer speaker before publishing.
- Before overwriting or deleting an existing episode's files, look at them; never write into another project's folder.
