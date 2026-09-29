# Where things are. Every engine script imports this first.
#   STORY_DIR   folder with script_data.py (screenplay) and project.py (titles, voices, notes)
#   EPISODE_DIR output folder for the film (audio/, visuals/, characters/, docs/, the MP4)
# Both come from environment variables (run_all.sh sets them); defaults: ./story and the current folder.
import os, sys

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
STORY_DIR = os.path.abspath(os.environ.get("STORY_DIR", "story"))
EPISODE_DIR = os.path.abspath(os.environ.get("EPISODE_DIR", "."))
if not os.path.exists(os.path.join(STORY_DIR, "script_data.py")):
    raise SystemExit(f"STORY_DIR={STORY_DIR} has no script_data.py (see README: 'Make your own film')")
if STORY_DIR not in sys.path:
    sys.path.insert(0, STORY_DIR)
for _d in ("", "docs", "audio/dialogue", "audio/voices", "audio/music", "audio/sfx", "visuals/shots",
           "visuals/storyboard", "characters/cards"):
    os.makedirs(os.path.join(EPISODE_DIR, _d), exist_ok=True)

import project as P      # noqa: E402  (story/project.py)

def ep(*parts):
    return os.path.join(EPISODE_DIR, *parts)
