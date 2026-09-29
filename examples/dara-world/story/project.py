# -*- coding: utf-8 -*-
"""Dara-world cast: settings to copy into a film's project.py (voices, profiles, character info)."""

TITLE_KH = "ពិភពដារ៉ា"
TITLE_EN = "The Dara World"
SOURCE = "Cast of the khmer-2d-character-creator master sheet"
OUT_MP4 = "dara_world.mp4"
CREDIT_KH = ""
CHAPTERS = {}

# VoxCPM2 voice-design prompts (designed once, then locked with lock_voices.py)
VOICES = {
  "dara":     "A Cambodian boy about eleven, bright curious clear child voice, kind and hopeful",
  "malis":    "A Cambodian girl about eleven, lively warm clear child voice, confident and cheerful",
  "sokha":    "An old Cambodian man about seventy, slow deep gentle wise male voice, calm, sometimes smiling",
  "veasna":   "A young Cambodian man about twenty, strong clear confident male voice, steady and protective",
  "bopha":    "A young Cambodian woman about twenty, graceful clear intelligent female voice, calm and kind",
  "jayavuth": "A Cambodian king about forty-five, deep powerful dignified male voice, serious but warm",
  "rotha":    "A Cambodian man about forty, smooth low calm male voice, clever and quietly menacing, never shouting",
  "sophea":   "A Cambodian mother about thirty-eight, warm caring natural female voice, patient, a little playful",
}
REF_TEXT = {k: "សួស្ដី! ថ្ងៃនេះយើងនឹងធ្វើដំណើរជាមួយគ្នា។" for k in VOICES}
CHOICE = {}
REUSE_LOCK = None
REUSE = {}
NARRATOR_FROM_REUSE = None
PROFILE = {
  "dara": ("male", "child", 1.0, "curious / hopeful / determined"),
  "malis": ("female", "child", 1.02, "cheerful / brave / caring"),
  "sokha": ("male", "70s", 0.9, "calm / wise / gently humorous"),
  "veasna": ("male", "20s", 0.98, "confident / protective"),
  "bopha": ("female", "20s", 0.96, "calm / intelligent / kind"),
  "jayavuth": ("male", "40s", 0.92, "dignified / serious / compassionate"),
  "rotha": ("male", "40s", 0.9, "smooth / clever / intimidating"),
  "sophea": ("female", "30s", 0.98, "warm / patient / playful"),
}
INFO = {
  "dara": ("Main young hero", "about 11", "small child, big head, large brown eyes", "hopeful",
           "cream short-sleeve shirt, red scarf + red waist sash, dark-brown cropped pants, brown sandals, "
           "small brown shoulder bag, dark-brown spiky hair"),
  "malis": ("Friend", "about 11", "small child", "gentle smile",
            "black hair in a high bun with a gold band and a white flower, cream blouse, deep-red skirt, "
            "gold drop earrings and bangles"),
  "sokha": ("Wise mentor", "about 70", "tall, slim, slight stoop", "calm, kind",
            "white hair in a topknot, long white beard, cream robe with brown over-robe and gold trim, spiral staff"),
  "veasna": ("Young warrior", "about 20", "athletic, not bulky", "confident",
             "black topknot, cream tunic, gold shoulder/forearm/shin guards, chest medallion, red waist cloth, "
             "gold belt, short sword at the hip"),
  "bopha": ("Princess, intelligent leader", "about 21", "slender, elegant", "calm smile",
            "very long black hair, small gold tiara, white strapless top with gold trim, maroon sampot, gold jewellery"),
  "jayavuth": ("King and protector", "about 45", "tallest, broad and strong", "serious but kind",
               "gold crown and breastplate, red cape, gold belt with front panel, dark trousers, black beard"),
  "rotha": ("Antagonist", "about 40", "lean, tall", "sly smile",
            "spiky tied black hair, pointed goatee, dark tunic with gold buttons, high-collared dark-red cape"),
  "sophea": ("Dara's mother, rice farmer", "about 38", "sturdy", "warm smile",
             "red-and-cream checked krama headwrap, indigo blouse with rolled sleeves, brown sampot with one red "
             "hem stripe, basket of greens on the hip"),
  "puppy": ("Animal companion", "young", "small dog", "happy", "cream-white with tan ears and back patch, red collar"),
  "monkey": ("Animal companion", "young", "small monkey", "cheeky", "brown fur, tan face and belly, curled tail"),
  "elephant": ("Animal companion", "baby", "small elephant", "happy", "grey, pink ears, gold forehead ornament"),
}
MUTES = []
CONTINUITY_NOTES = ["[OK] Every Dara-world character uses its locked spec from engine/cast_dara.py."]
