# -*- coding: utf-8 -*-
"""Project settings for the starter story."""
TITLE_KH = "រឿងគំរូ"
TITLE_EN = "A Starter Story"
SOURCE = "template"
OUT_MP4 = "starter_story.mp4"
CREDIT_KH = ""

CHAPTERS = {1: ("ថ្ងៃមួយនៅភូមិ", "A Day in the Village")}

VOICES = {
  "narrator": "A Cambodian woman in her forties, calm warm clear storytelling voice, slow and gentle",
  "sam": "A Cambodian young man about twenty-five, warm clear medium male voice, sincere",
  "soy": "A Cambodian young woman about twenty-two, soft gentle sweet female voice, calm and kind",
}
REF_TEXT = {
  "narrator": "កាលពីដើម នៅក្នុងភូមិមួយ មានមនុស្សជាច្រើន ដែលខំប្រឹងធ្វើការ ដើម្បីចិញ្ចឹមគ្រួសារ។",
  "sam": "ខ្ញុំឈ្មោះសម។ ខ្ញុំមកពីស្រុកស្រែ ហើយខ្ញុំចង់រកការងារសុចរិត ដើម្បីចិញ្ចឹមប្រពន្ធខ្ញុំ។",
  "soy": "ខ្ញុំឈ្មោះសយ។ ខ្ញុំចេះបោកខោអាវ ចម្អិនម្ហូប ហើយខ្ញុំតែងតែនៅក្បែរប្ដីខ្ញុំជានិច្ច។",
}
CHOICE = {}                      # empty = pick the best candidate automatically
REUSE_LOCK = None
REUSE = {}
NARRATOR_FROM_REUSE = None
PROFILE = {
  "narrator": ("female", "40s", 0.94, "warm-serious"),
  "sam": ("male", "25", 0.98, "hopeful / tired / determined"),
  "soy": ("female", "22", 0.96, "gentle / hopeful"),
}
INFO = {   # character bible notes: id -> (role, age, body type, default expression, costume notes)
  "sam": ("Young farmer", "about 25", "slim", "calm", "blue-grey shirt, brown rolled trousers, red-white krama"),
  "soy": ("His wife", "about 22", "small, slim", "gentle", "rose blouse, purple woven sarong, green-white krama"),
}
MUTES = []
CONTINUITY_NOTES = []
