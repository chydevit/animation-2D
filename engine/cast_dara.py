# -*- coding: utf-8 -*-
"""The Dara world: locked 2D rigs for the cast of the khmer-2d-character-creator master sheet.

    Dara · Malis · Lok Ta Sokha · Veasna · Princess Bopha · King Jayavuth · Rotha · Mother Sophea
    puppy · monkey · baby elephant

Design locks: https://github.com/chydevit/khmer-2d-character-creator (references/cast-bible.md).
Dara, Malis and Lok Ta Sokha match the "Keep Growing, Never Stop" film exactly.

Use in a film: in story/story_chars.py write

    import cast_dara
    cast_dara.register()                 # adds the ids below to chars.CAST
    # or cast_dara.register(["dara", "malis", "puppy"])

Never change these specs between scenes; add a costume variant with chars.variant() instead.
"""
import chars
from chars import spec

KID = dict(head_r=17.5, head_wx=1.04, jaw=0.0, shoulder=27, waist=24, hip=25, torso_len=33, leg_len=47,
           arm_up=18, arm_lo=17, arm_w=6.6, leg_w=9.0, eye_scale=1.42, blush=0.3, brow_w=1.1)
KRAMA_RED_CREAM = ("#ab2d2a", "#efe2c2")

DARA_WORLD = {
  # main young hero — height unit 1.00
  "dara": spec(**KID, H=128, skin="#dea57a", hair="#3a2317", eye="#5a3016", lips="#b0604e",
               shirt="#efe2c2", shirt2="#e2d2ac", shirt_style="tunic", pants="#4b2a24", pants_style="cropped",
               shoes="sandal", shoe_col="#6b4226", hair_style="boy_spiky",
               extras=["scarf_red", "sash_waist", "shoulder_bag"], sash="#ab2d2a", bag="#7a4e2c"),
  # friend — 0.97
  "malis": spec(**dict(KID, shoulder=25, waist=21, hip=25, torso_len=32, leg_len=46, head_r=17.0, arm_w=6.0, leg_w=8.4),
                H=124, skin="#e2ab82", hair="#1a1210", eye="#4a2812", lips="#b85a50", female=True,
                shirt="#f4ecdc", shirt_style="blouse", pants_style="skirt", skirt="#8e2f36", skirt2="#c9a44a",
                shoes="sandal", shoe_col="#c98a3a", hair_style="bun_top",
                extras=["flower_hair", "necklace", "earrings_drop", "bangles"]),
  # wise mentor — white topknot, long beard, spiral staff, slight stoop
  "sokha": spec(H=172, head_r=14.6, jaw=0.2, shoulder=36, waist=30, hip=33, torso_len=54, leg_len=80, arm_w=8.0,
                leg_w=11.5, skin="#d9a077", hair="#eeeae2", eye="#4a2812", shirt="#efe6d0", shirt_style="blouse_long",
                pants_style="skirt", skirt="#ece2cc", skirt2="#d8cbb0", shoes="sandal", shoe_col="#5a3a22",
                hair_style="topknot_white", facial="beard_long", extras=["robe_over", "staff"], robe="#7a5534",
                age=1.0, bags=0.5, blush=0.08, eye_scale=1.08),
  # young warrior — 1.45: topknot, gold shoulder/forearm/shin guards, chest medallion, sword at the hip
  "veasna": spec(H=186, head_r=15.2, jaw=0.3, shoulder=42, waist=31, hip=33, torso_len=58, leg_len=90,
                 arm_up=31, arm_lo=28, arm_w=9.6, leg_w=13.0, skin="#c98f5e", hair="#15100d", eye="#4a2812",
                 lips="#a45a4a", shirt="#efe2c2", shirt2="#e2d2ac", shirt_style="tunic", pants="#4b2f22",
                 pants_style="long", shoes="sandal", shoe_col="#6b4226", hair_style="topknot_black",
                 extras=["sash_waist", "gold_belt", "shoulder_guards", "chest_medallion", "arm_guards", "shin_guards",
                         "sword_hip"], sash="#9e2a2a", eye_scale=1.18, blush=0.08, brow_w=1.25),
  # royal leader — 1.40: very long hair, small gold tiara, white strapless top with gold trim, maroon sampot
  "bopha": spec(H=179, head_r=14.8, jaw=0.05, shoulder=33, waist=24, hip=31, torso_len=53, leg_len=86, arm_w=7.2,
                leg_w=10.5, skin="#dfa77c", hair="#120d0b", eye="#4a2812", lips="#b0504a", female=True,
                shirt="#fbf6ec", shirt_style="strapless", pants_style="skirt", skirt="#7e2632", skirt2="#d4a93c",
                skirt_stripes=3, shoes="sandal", shoe_col="#d4a93c", hair_style="long_straight",
                extras=["tiara_gold", "earrings_drop", "armbands_gold", "bangles", "gold_belt", "necklace"],
                eye_scale=1.3, blush=0.22),
  # king — 1.60, tallest: gold crown and breastplate, red cape, beard + moustache
  "jayavuth": spec(H=205, head_r=16.2, jaw=0.55, shoulder=52, waist=40, hip=40, torso_len=64, leg_len=96,
                   arm_up=33, arm_lo=30, arm_w=12.5, leg_w=16.0, skin="#b97a4a", hair="#120d0b", eye="#3a2010",
                   lips="#9a4a40", shirt="#c9a13f", shirt_style="armor", pants="#4b2f22", pants_style="long",
                   shoes="sandal", shoe_col="#6b4226", hair_style="topknot_black", facial="beard_full",
                   extras=["cape", "crown_gold", "shoulder_guards", "sash_waist", "front_panel", "gold_belt",
                           "armbands_gold", "arm_guards"], cape="#9e2a2a", sash="#9e2a2a",
                   eye_scale=1.1, blush=0.0, brow_w=1.5, age=0.35),
  # antagonist — 1.52: spiky tied hair, goatee, dark tunic, high-collared dark red cape
  "rotha": spec(H=195, head_r=15.0, jaw=0.45, shoulder=44, waist=30, hip=32, torso_len=62, leg_len=92, arm_w=9.0,
                leg_w=12.0, skin="#c28a5c", hair="#100c0a", eye="#2e1a10", lips="#8e4a40", shirt="#3b2b30",
                shirt_style="mandarin", pants="#26211f", pants_style="long", shoes="shoe", shoe_col="#1e1614",
                hair_style="spiky_tied", facial="goatee", extras=["cape", "cape_collar", "gold_belt"],
                cape="#7a1f26", eye_scale=0.95, blush=0.0, brow_w=1.4, age=0.3),
  # Dara's mother, rice farmer — 1.38: checked krama headwrap, indigo blouse, one red stripe at the hem
  "sophea": spec(H=177, head_r=15.0, jaw=0.1, shoulder=35, waist=28, hip=34, torso_len=54, leg_len=84, arm_w=7.8,
                 leg_w=11.0, skin="#c98f5e", hair="#1b1411", eye="#4a2812", lips="#a8544c", female=True,
                 shirt="#4f5f86", shirt2="#3f4d70", shirt_style="work_rolled", pants_style="skirt", skirt="#5a3a28",
                 skirt2="#8e2f36", skirt_stripes=1, shoes="sandal", shoe_col="#6b4226", hair_style="bun",
                 extras=["headwrap_krama", "bracelet_thread", "basket_hip"], krama=KRAMA_RED_CREAM,
                 age=0.3, blush=0.15, eye_scale=1.12),
  # animal companions (drawn by the animal rig in chars.py)
  "puppy": spec(H=52, head_r=12.0, animal="dog", skin="#f3ead8", hair="#c98a4f", eye="#3a2010"),
  "monkey": spec(H=48, head_r=11.0, animal="monkey", skin="#e2b98a", hair="#8a5a34", eye="#3a2010"),
  "elephant": spec(H=72, head_r=16.0, animal="elephant", skin="#9aa3ad", hair="#7d8691", eye="#5f7f99"),
}

NAMES = {"dara": ("ដារ៉ា", "Dara"), "malis": ("ម្លិះ", "Malis"), "sokha": ("លោកតា សុខា", "Lok Ta Sokha"),
         "veasna": ("វាសនា", "Veasna"), "bopha": ("ព្រះនាង បុប្ផា", "Princess Bopha"),
         "jayavuth": ("ស្ដេច ជ័យវុធ", "King Jayavuth"), "rotha": ("រដ្ឋា", "Rotha"),
         "sophea": ("ម្ដាយ សុភា", "Mother Sophea"), "puppy": ("កូនឆ្កែ", "Puppy"),
         "monkey": ("ស្វា", "Monkey"), "elephant": ("កូនដំរី", "Baby elephant")}


def register(ids=None):
    """Add the Dara-world rigs (all, or just `ids`) to chars.CAST. Returns the ids added."""
    ids = list(ids or DARA_WORLD)
    chars.CAST.update({k: DARA_WORLD[k] for k in ids})
    return ids
