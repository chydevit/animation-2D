# -*- coding: utf-8 -*-
"""Cast sheets for the Dara world (no scenes). Draw them with:
    STORY_DIR=examples/dara-world/story EPISODE_DIR=/tmp/dara-world python engine/sheet.py all"""
import cast_dara

CHARACTERS = {k: dict(kh=kh, en=en) for k, (kh, en) in cast_dara.NAMES.items()}
SCENES = []
