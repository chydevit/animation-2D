# 2D cut-out character rig for the film. Characters are drawn facing screen-right in local
# centimetre units (origin = between the feet on the ground, y down) and flipped for facing left.
import math
import skia
from gfx import Ctx, rgb, mix, shade, light, poly, smooth, rrect, lin_grad, ang, rot_pt, lerp, ease, OUTLINE

SKIN_PHANIT = "#d39a68"
KRAMA_RED = ("#b3312c", "#f1eadb")
KRAMA_BLUE = ("#2f5d8a", "#eee9dc")

GOLD = "#d4a93c"
TIED_HAIR = ("bun", "braids", "gray_bun", "long_back", "chignon_high", "bun_top", "topknot_white",
             "topknot_black", "long_straight")

# ───────────────────────────────────────────────────────────── character specs
BASE = dict(H=165, head_r=14.5, head_wx=1.0, jaw=0.0, shoulder=38, waist=31, hip=32, belly=0,
            torso_len=52, leg_len=78, arm_up=29, arm_lo=26, arm_w=9.0, leg_w=12.5,
            skin="#c98f5e", hair="#1b1411", hair2=None, eye="#4a2812", lips="#a45a4a",
            shirt="#f2eee4", shirt_style="short", shirt2="#ffffff", pants="#34405c", pants_style="long",
            shoes="sandal", shoe_col="#6b4226", hair_style="neat_side", facial="none",
            extras=[], age=0.0, bags=0.0, blush=0.25, brow_w=1.0, eye_scale=1.0, female=False,
            skirt=None, skirt2=None, krama=KRAMA_RED, weak=0.0)

def spec(**kw):
    s = dict(BASE); s.update(kw); return s

KRAMA_GREEN = ("#3f6e4a", "#e9e4d2")
KRAMA_PURPLE = ("#6a3f6e", "#ece3dc")

def variant(base, **kw):
    s = dict(base); s.update(kw); return s

# LOCKED designs (see docs/character_bible.json). Only costume variants listed below may differ,
# and a variant keeps the face, hair, skin and body of its base character.
_SAM = spec(H=166, head_r=14.3, jaw=0.15, shoulder=36, waist=29, hip=30, torso_len=51, leg_len=80,
            arm_w=8.2, leg_w=11.8, skin="#b9804d", hair="#171210", shirt="#8ea4b8", shirt2="#7a90a4",
            shirt_style="short_collar", pants="#5b4632", pants_style="rolled", hair_style="neat_side",
            extras=["krama_neck"], krama=KRAMA_RED, age=0.05, eye_scale=1.05, blush=0.12)
_SOY = spec(H=154, head_r=13.9, shoulder=31, waist=25, hip=30, torso_len=46, leg_len=74, arm_w=7.0, leg_w=10.6,
            skin="#c48c5c", hair="#15100d", shirt="#d98f8a", shirt2="#c47a76", shirt_style="blouse",
            pants_style="skirt", skirt="#4d3a5c", skirt2="#6e5580", hair_style="bun", female=True,
            extras=["krama_shoulder"], krama=KRAMA_GREEN, lips="#a8544c", eye_scale=1.08, blush=0.22)

CAST = {
  "sam": _SAM,
  "sam_prison": variant(_SAM, shirt="#8c8f86", shirt2="#77796f", shirt_style="work_rolled", pants="#6f7168",
                        pants_style="rolled", extras=[], facial="stubble", bags=0.35),
  "sam_ragged": variant(_SAM, shirt="#6f7c86", shirt2="#5d6870", shirt_style="short_open", pants="#46382a",
                        extras=["krama_neck", "patches"], facial="stubble", bags=0.6, weak=0.25, hair_style="messy"),
  "soy": _SOY,
  "soy_preg": variant(_SOY, belly=9, shirt="#cf9a90", extras=["krama_shoulder"]),
  "mey": spec(H=169, head_r=14.6, jaw=0.4, shoulder=41, waist=33, hip=33, torso_len=53, leg_len=80, arm_w=9.6,
              leg_w=12.8, skin="#a56a3b", hair="#1c1612", shirt="#2f5f8a", shirt2="#284f73",
              shirt_style="work_rolled", pants="#2f2f2c", pants_style="rolled", hair_style="short",
              extras=["krama_neck"], krama=KRAMA_BLUE, age=0.2, blush=0.06),
  "mom": spec(H=157, head_r=14.0, shoulder=33, waist=27, hip=32, torso_len=47, leg_len=74, arm_w=7.3,
              leg_w=10.8, skin="#b98552", hair="#1a1310", shirt="#e0b04a", shirt2="#c7973a",
              shirt_style="blouse", pants_style="skirt", skirt="#7a3a2a", skirt2="#a2553c", hair_style="long_back",
              female=True, lips="#9c5046", age=0.15, blush=0.2),
  "kimleang": spec(H=158, head_r=14.2, jaw=0.2, shoulder=34, waist=31, hip=35, belly=3, torso_len=48, leg_len=73,
                   arm_w=7.8, leg_w=11, skin="#caa06f", hair="#120e0c", shirt="#f2efe6", shirt_style="blouse_long",
                   pants_style="skirt", skirt="#2a3b5e", skirt2="#c9a44a", hair_style="chignon_high", female=True,
                   extras=["earrings", "watch"], lips="#8e3a36", age=0.45, bags=0.2, blush=0.05),
  "tasan": spec(H=158, head_r=14.4, jaw=0.3, shoulder=34, waist=29, hip=29, torso_len=49, leg_len=74, arm_w=7.6,
                leg_w=10.8, skin="#9c6a40", hair="#b9b3aa", shirt="#d8d2c2", shirt_style="singlet",
                pants="#4a4038", pants_style="rolled", hair_style="messy", hair2="#b9b3aa", facial="stubble",
                extras=["krama_neck"], krama=KRAMA_RED, age=0.95, bags=0.6, blush=0.0),
  "sau": spec(H=170, head_r=14.3, jaw=0.45, shoulder=39, waist=30, hip=30, torso_len=53, leg_len=81, arm_w=8.8,
              leg_w=12.2, skin="#9e6538", hair="#110d0b", shirt="#2b2a2e", shirt2="#6b2323",
              shirt_style="short_open", pants="#3d4a3a", pants_style="long", hair_style="spiky",
              facial="stubble", extras=["scar"], age=0.15, bags=0.3, blush=0.0, brow_w=1.25),
  "broker": spec(H=150, head_r=13.8, shoulder=31, waist=29, hip=32, torso_len=45, leg_len=69, arm_w=7.0,
                 leg_w=10.4, skin="#a8744a", hair="#c9c3ba", shirt="#6d4a7a", shirt_style="blouse_long",
                 pants_style="skirt", skirt="#2e2a26", skirt2="#5a4a3a", hair_style="gray_bun", female=True,
                 extras=["betel_basket"], age=0.85, bags=0.5, blush=0.05, lips="#8a2f28"),
  "hok": spec(H=168, head_r=15.2, jaw=0.3, head_wx=1.06, shoulder=42, waist=41, hip=39, belly=9, torso_len=55,
              leg_len=76, arm_w=9.8, leg_w=13.8, skin="#d6ad80", hair="#0f0c0b", shirt="#5a1f24", shirt2="#e8dfc8",
              shirt_style="short_collar", pants="#2a2622", pants_style="long", shoes="shoe", shoe_col="#1e1410",
              hair_style="slick", facial="mustache_thin", extras=["watch", "ring"], age=0.6, bags=0.3, blush=0.1),
  "police": spec(H=170, head_r=14.6, jaw=0.4, shoulder=40, waist=33, hip=33, torso_len=54, leg_len=80,
                 arm_w=9.2, leg_w=12.8, skin="#b98253", shirt="#b39c63", shirt2="#9a8452", shirt_style="uniform",
                 pants="#a58f5a", shoes="shoe", shoe_col="#2a1c14", hair_style="short", facial="mustache",
                 extras=["cap_police", "belt_black", "whistle"], age=0.35, blush=0.05),
  "police2": spec(H=167, head_r=14.2, shoulder=38, waist=30, hip=30, torso_len=52, leg_len=79,
                  skin="#c28a58", shirt="#b39c63", shirt2="#9a8452", shirt_style="uniform",
                  pants="#a58f5a", shoes="shoe", shoe_col="#2a1c14", hair_style="short",
                  extras=["cap_police", "belt_black"], age=0.05, blush=0.12),
  "chhuoy": spec(H=161, head_r=14.4, jaw=0.2, shoulder=35, waist=30, hip=30, torso_len=50, leg_len=75, arm_w=7.8,
                 leg_w=11.2, skin="#a0703f", hair="#d6d1c8", shirt="#8c8f86", shirt2="#77796f",
                 shirt_style="work_rolled", pants="#6f7168", pants_style="rolled", hair_style="short",
                 facial="beard_white", age=1.0, bags=0.7, blush=0.0),
  "huor": spec(H=172, head_r=15.0, jaw=0.6, head_wx=1.08, shoulder=45, waist=36, hip=35, torso_len=55, leg_len=80,
               arm_w=11, leg_w=14, skin="#8f5a32", hair="#1a1512", shirt="#8c8f86", shirt_style="work_rolled",
               pants="#6f7168", pants_style="rolled", hair_style="bald_sides", facial="stubble", age=0.4, blush=0),
  "suos": spec(H=164, head_r=14.2, jaw=0.35, shoulder=39, waist=31, hip=31, torso_len=51, leg_len=78, arm_w=9,
               leg_w=12, skin="#a26b3c", hair="#141110", shirt="#8c8f86", shirt_style="work_rolled",
               pants="#6f7168", pants_style="rolled", hair_style="spiky", facial="stubble", age=0.25, blush=0),
  "guard": spec(H=171, head_r=14.5, jaw=0.35, shoulder=40, waist=33, hip=33, torso_len=54, leg_len=80, arm_w=9.2,
                leg_w=12.8, skin="#b07a4a", shirt="#56603e", shirt2="#48512f", shirt_style="uniform",
                pants="#4f5838", shoes="shoe", shoe_col="#1e1812", hair_style="short",
                extras=["cap_guard", "belt_black"], age=0.3, blush=0.04),
  "yaykan": spec(H=149, head_r=13.9, shoulder=31, waist=28, hip=31, torso_len=45, leg_len=68, arm_w=6.9,
                 leg_w=10.2, skin="#c49a72", hair="#e3dfd8", shirt="#f4f1ea", shirt_style="blouse_long",
                 pants_style="skirt", skirt="#3e5a3a", skirt2="#c9a44a", hair_style="gray_bun", female=True,
                 extras=["krama_shoulder", "necklace"], krama=KRAMA_PURPLE, age=1.0, bags=0.55, blush=0.12,
                 lips="#a86a5e"),
  "worker": spec(H=165, head_r=14.6, head_wx=1.05, shoulder=37, waist=31, hip=31, torso_len=51, leg_len=77,
                 skin="#b77c48", hair="#1d1612", shirt="#c9772f", shirt2="#b0652a", shirt_style="work_rolled",
                 pants="#3a3632", pants_style="rolled", hair_style="wavy", extras=["headband_white"], age=0.05,
                 blush=0.15),
  "worker2": spec(H=162, head_r=14.2, jaw=0.3, shoulder=36, waist=31, hip=31, torso_len=50, leg_len=76,
                  skin="#9a6236", hair="#1b1512", shirt="#6d7f55", shirt2="#5a6a45", shirt_style="singlet",
                  pants="#4b3b2c", pants_style="rolled", hair_style="short", facial="mustache", age=0.4, blush=0),
  "worker3": spec(H=160, head_r=14.2, shoulder=35, waist=29, hip=30, torso_len=49, leg_len=76,
                  skin="#c28a58", hair="#221a15", shirt="#e9e2cf", shirt_style="short", pants="#34405c",
                  pants_style="rolled", hair_style="short", age=0.1, blush=0.18),
  "sengly": spec(H=165, head_r=14.8, jaw=0.2, head_wx=1.04, shoulder=38, waist=35, hip=35, belly=4, torso_len=52,
                 leg_len=76, arm_w=8.8, leg_w=12.6, skin="#dcb68c", hair="#a9a49c", shirt="#f3f1ea",
                 shirt_style="mandarin", pants="#3a3a44", pants_style="long", shoes="shoe", shoe_col="#1e1a18",
                 hair_style="slick", hair2="#a9a49c", extras=["glasses"], age=0.8, bags=0.35, blush=0.12),
  "sengan": spec(H=167, head_r=14.2, shoulder=36, waist=29, hip=30, torso_len=52, leg_len=80, arm_w=8,
                 leg_w=11.6, skin="#dfb98e", hair="#141110", shirt="#f4f2ec", shirt_style="short_collar",
                 pants="#5a5448", shoes="shoe", shoe_col="#3a2618", hair_style="neat_side",
                 extras=["pocket_pen"], age=0.15, blush=0.16),
  "senghong": spec(H=172, head_r=14.4, jaw=0.25, shoulder=38, waist=30, hip=30, torso_len=54, leg_len=82,
                   arm_w=8.4, leg_w=12, skin="#e2bd92", hair="#0d0b0a", shirt="#c9b27a", shirt2="#f7f3e8",
                   shirt_style="jacket", pants="#8a7a5a", shoes="shoe", shoe_col="#5a2e18", hair_style="pompadour",
                   extras=["watch", "ring"], age=0.05, blush=0.1, brow_w=1.15),
  "yeng": spec(H=168, head_r=14.9, jaw=0.35, head_wx=1.05, shoulder=40, waist=36, hip=35, belly=5, torso_len=53,
               leg_len=78, arm_w=9.2, leg_w=13, skin="#c69366", hair="#141110", hair2="#5a5650",
               shirt="#e8dcc0", shirt2="#fbfaf5", shirt_style="jacket", pants="#e0d4b8", shoes="shoe",
               shoe_col="#3a2618", hair_style="slick", facial="mustache", extras=["tie", "glasses"], age=0.45,
               bags=0.25, blush=0.1),
  "nara": spec(H=167, head_r=14.5, jaw=0.2, shoulder=37, waist=31, hip=31, torso_len=52, leg_len=78,
               skin="#b98a5c", hair="#2a2522", hair2="#8e8a84", shirt="#f6f6f2", shirt2="#dfe4e8",
               shirt_style="coat", pants="#3e4550", shoes="shoe", shoe_col="#2a1c14", hair_style="short",
               extras=["glasses", "stethoscope"], age=0.6, bags=0.5, blush=0.02),
  "oknha": spec(H=166, head_r=15.3, jaw=0.35, head_wx=1.07, shoulder=41, waist=40, hip=39, belly=10, torso_len=54,
                leg_len=75, arm_w=9.8, leg_w=13.6, skin="#cfa47a", hair="#b0aaa0", shirt="#f7f4ea",
                shirt_style="mandarin", pants="#4a2a55", pants_style="rolled", shoes="shoe", shoe_col="#1c1410",
                hair_style="bald_sides", facial="mustache", extras=["medal", "ring"], age=0.95, bags=0.45, blush=0.1),
  "minister": spec(H=173, head_r=14.3, shoulder=38, waist=30, hip=30, torso_len=54, leg_len=82, arm_w=8.4,
                   leg_w=12, skin="#c89468", hair="#0f0d0c", shirt="#b8bcc0", shirt2="#fbfaf5",
                   shirt_style="jacket", pants="#a9adb2", shoes="shoe", shoe_col="#1a1412",
                   hair_style="neat_side", extras=["tie_navy"], age=0.1, blush=0.14),
}

# ───────────────────────────────────────────────────────────── poses
# Angles in degrees. sh = upper arm from straight down (+ = swings forward), el = elbow bend (+ = forearm
# folds forward/up). hip = thigh from straight down (+ forward), kn = knee bend (shin folds back).
STAND = dict(torso=0, head=0, nsh=6, nel=10, fsh=4, fel=12, nhip=2, nkn=0, fhip=-2, fkn=0,
             pdy=0, seat=0, nhand="open", fhand="open", prop=None)

def P(**kw):
    d = dict(STAND); d.update(kw); return d

_FLOOR = dict(seat=1, floor=1, nhip=86, nkn=158, fhip=82, fkn=156)
_KNEEL = dict(kneel=1, nhip=2, nkn=96, fhip=-2, fkn=94)
POSES = {
  "stand": P(),
  "sit": P(**_FLOOR, torso=4, ik_n="knee", ik_f="knee_f", nhand="flat", fhand="flat"),
  "sit_sad": P(**_FLOOR, torso=20, head=20, ik_n="knee", ik_f="knee_f", nhand="flat", fhand="flat"),
  "sit_work": P(**_FLOOR, torso=16, head=16, nsh=46, nel=46, fsh=50, fel=40, nhand="fist", fhand="fist",
                anim="work_small"),
  "sit_pray": P(**_FLOOR, torso=8, head=12, ik_n="chest_c", ik_f="chest_c", nhand="flat", fhand="flat"),
  "desk": P(**_FLOOR, torso=10, head=6, nsh=42, nel=48, fsh=46, fel=44),
  "write": P(**_FLOOR, torso=16, head=16, nsh=44, nel=52, fsh=48, fel=40, fhand="fist", prop="pen", anim="write"),
  "look_up": P(**_FLOOR, torso=6, head=-4, nsh=42, nel=48, fsh=46, fel=44),
  "kneel": P(**_KNEEL, torso=6, head=8, nsh=20, nel=30, fsh=18, fel=34),
  "kneel_sampeah": P(**_KNEEL, torso=10, head=12, ik_n="chest_c", ik_f="chest_c", nhand="flat", fhand="flat"),
  "kneel_grief": P(**_KNEEL, torso=26, head=24, ik_n="face", ik_f="face", nhand="open", fhand="open"),
  "offer": P(nsh=62, nel=24, nhand="open", prop="jar"),
  "offer_money": P(nsh=62, nel=24, nhand="open", prop="money"),
  "hush": P(ik_n="mouth", nhand="point_up", head=4),
  "shock": P(torso=-6, head=-5, nsh=28, nel=96, fsh=24, fel=100, nhand="open", fhand="open"),
  "head_down": P(torso=8, head=20, nsh=4, nel=8, fsh=2, fel=10),
  "point": P(nsh=84, nel=4, nhand="point"),
  "gesture_sit": P(nsh=40, nel=26, nhand="open"),
  "sampeah": P(ik_n="chest_c", ik_f="chest_c", nhand="flat", fhand="flat", head=8, torso=6),
  "arms_up": P(nsh=120, nel=40, fsh=110, fel=44, torso=-4, head=-4),
  "hand_chest": P(ik_n="chest_n", nhand="flat"),
  "hand_belly": P(**_FLOOR, torso=0, head=10, ik_n="belly", nhand="flat", fsh=12, fel=44),
  "stop_hand": P(nsh=78, nel=38, nhand="flat_up"),
  "arms_crossed": P(ik_n="cross_n", ik_f="cross_f", nhand="fist", fhand="fist"),
  "hands_face": P(ik_n="face", ik_f="face", nhand="open", fhand="open", head=14, torso=6),
  "fists": P(torso=4, head=4, nsh=10, nel=24, fsh=8, fel=26, nhand="fist", fhand="fist", anim="shake"),
  "work": P(torso=38, head=22, nsh=70, nel=30, fsh=76, fel=26, nhand="fist", fhand="fist", anim="work"),
  "hoe": P(torso=30, head=16, nsh=70, nel=30, fsh=76, fel=26, nhand="fist", fhand="fist", anim="hoe", prop="hoe"),
  "sweep": P(torso=24, head=18, nsh=40, nel=20, fsh=52, fel=16, nhand="fist", fhand="fist", prop="broom",
             anim="sweep"),
  "stir": P(torso=14, head=10, nsh=70, nel=40, fsh=64, fel=46, nhand="fist", fhand="fist", prop="paddle",
            anim="stir"),
  "carry": P(torso=10, head=6, ik_n="shoulder_top", ik_f="shoulder_top2", nhand="fist", fhand="fist",
             prop="sack", hold=True),
  "hold_cup": P(ik_n="chest_f", ik_f="chest_c", nhand="fist", fhand="flat", prop="cup", head=6),
  "cyclo": P(seat=1, cyclo=1, torso=14, head=-4, nsh=38, nel=30, fsh=36, fel=30, nhand="fist", fhand="fist",
             nhip=62, nkn=78, fhip=40, fkn=96),
  "cyclo_sampeah": P(seat=1, cyclo=1, torso=8, head=8, ik_n="chest_c", ik_f="chest_c", nhand="flat",
                     fhand="flat", nhip=62, nkn=78, fhip=40, fkn=96),
  "bed": P(lie=True, bed=True, nsh=12, nel=18, fsh=10, fel=24, head=-6),
  "lie": P(lie=True, nsh=12, nel=18, fsh=10, fel=24, head=0),
}
BASE_POSES = {"hoe", "stand", "sit", "sit_sad", "sit_work", "sit_pray", "desk", "write", "look_up", "kneel",
              "kneel_sampeah", "kneel_grief", "work", "sweep", "stir", "carry", "hold_cup", "cyclo", "bed", "lie",
              "hand_belly", "head_down"}
SEATED = {"sit", "sit_sad", "sit_work", "sit_pray", "desk", "write", "look_up", "hand_belly"}


# ───────────────────────────────────────────────────────────── expressions
EXPR = {
  "neutral": dict(bh=0.0, ba=0.0, eo=1.0, lo=0.0, mc=0.0, mouth="closed"),
  "happy": dict(bh=0.03, ba=2, eo=0.9, lo=0.25, mc=0.55, mouth="smile"),
  "worried": dict(bh=0.03, ba=14, eo=1.02, lo=0.0, mc=-0.25, mouth="closed"),
  "sad": dict(bh=0.0, ba=18, eo=0.72, lo=0.1, mc=-0.45, mouth="closed"),
  "angry": dict(bh=-0.04, ba=-18, eo=0.86, lo=0.15, mc=-0.35, mouth="closed"),
  "shock": dict(bh=0.12, ba=6, eo=1.28, lo=0.0, mc=-0.1, mouth="surprisedO"),
  "serious": dict(bh=-0.02, ba=-7, eo=0.92, lo=0.08, mc=-0.12, mouth="closed"),
  "tired": dict(bh=-0.01, ba=8, eo=0.68, lo=0.12, mc=-0.18, mouth="closed"),
  "smug": dict(bh=-0.02, ba=-9, eo=0.78, lo=0.2, mc=0.22, mouth="closed"),
  "cry": dict(bh=0.0, ba=22, eo=0.55, lo=0.25, mc=-0.55, mouth="closed", tears=True),
  "brave": dict(bh=0.0, ba=-5, eo=1.0, lo=0.0, mc=0.05, mouth="closed"),
  "calm": dict(bh=0.0, ba=3, eo=0.88, lo=0.1, mc=0.12, mouth="closed"),
}
EMO_KEYS = [
  ("cry", "cry", "sob", "tears", "weep", "grieving"),
  ("shock", "shock", "startled", "stunned", "freeze", "gasp", "eyes wide"),
  ("angry", "angry", "furious", "shout", "snapping", "sharp", "harsh", "defiant", "disgusted"),
  ("smug", "smug", "thin smile", "cold", "controlled", "false sympathy", "lying", "dismissive", "condescending",
   "manipulative", "bribing", "generous act", "evasive", "eager"),
  ("sad", "sad", "broken", "pained", "devastated", "tender", "weary", "ashamed", "grave"),
  ("worried", "worried", "nervous", "anxious", "uneasy", "scared", "hesitant", "distressed", "confused",
   "desperate", "pleading", "begging", "frightened", "overwhelmed", "tempted", "shaky", "hurt", "cautious"),
  ("tired", "tired", "weak"),
  ("brave", "brave", "firm", "resolute", "determined", "steady", "strong", "passionate", "accusing", "earnest",
   "clear", "urgent", "protective", "commanding", "stern", "official", "authoritative", "challenging", "blocking",
   "piercing", "warning", "quietly defiant"),
  ("serious", "serious", "tense", "bitter", "cynical", "probing", "wary", "secretive", "low", "alert"),
  ("calm", "calm", "gentle", "kind", "polite", "reflective", "hopeful", "at peace", "accepting", "dignified",
   "thoughtful", "innocent", "curious", "wise", "honest"),
]

def expr_for(emo):
    e = (emo or "").lower()
    for row in EMO_KEYS:
        for k in row[1:]:
            if k in e:
                return row[0]
    return "neutral"

# ───────────────────────────────────────────────────────────── mouth shapes
# (width, open height, roundness, teeth)
MOUTHS = {
  "closed": (1.0, 0.0, 0.0, 0), "small": (0.72, 0.28, 0.2, 0), "wide": (1.12, 0.55, 0.0, 1),
  "A": (0.95, 0.85, 0.15, 1), "E": (1.08, 0.42, 0.0, 1), "I": (1.04, 0.26, 0.0, 1),
  "O": (0.62, 0.72, 0.9, 0), "U": (0.46, 0.36, 1.0, 0), "smile": (1.08, 0.0, 0.0, 0),
  "surprisedO": (0.56, 0.9, 1.0, 0),
}


class Rig:
    def __init__(self, name):
        self.name = name
        self.s = CAST[name]

    # ------------------------------------------------------------ geometry helpers
    def dims(self):
        s = self.s
        return s["leg_len"], s["torso_len"], s["head_r"]

    def limb_dir(self, a_deg):
        a = ang(a_deg)
        return (math.sin(a), math.cos(a))

    def ik(self, S, T, a, b, bend=1):
        dx, dy = T[0] - S[0], T[1] - S[1]
        d = max(min(math.hypot(dx, dy), a + b - 0.01), abs(a - b) + 0.01)
        base = math.atan2(dy, dx)
        cosA = (a * a + d * d - b * b) / (2 * a * d)
        A = math.acos(max(-1, min(1, cosA)))
        cands = [(S[0] + a * math.cos(base + sg * A), S[1] + a * math.sin(base + sg * A)) for sg in (1, -1)]
        # natural elbow: the lower one (elbows hang down), tie-break toward the back
        E = max(cands, key=lambda e: e[1] - 0.3 * e[0])
        W = (E[0] + b * (dx / math.hypot(dx, dy) if (dx or dy) else 0) * 0, 0)
        # wrist = point at distance b from E toward T
        vx, vy = T[0] - E[0], T[1] - E[1]
        L = math.hypot(vx, vy) or 1
        W = (E[0] + vx / L * b, E[1] + vy / L * b)
        return E, W

    # ------------------------------------------------------------ skeleton
    def skeleton(self, p, t=0.0, breath=0.0, walk=None):
        s = self.s
        if s.get("animal"):
            return self.animal_skeleton(t, walk)
        leg, tl, r = self.dims()
        thigh, shin = leg * 0.5, leg * 0.5
        # legs
        nhip, nkn, fhip, fkn = p["nhip"], p["nkn"], p["fhip"], p["fkn"]
        bob = 0.0
        cyc = (p.get("cyclo", 0) or 0) > 0.5
        if cyc and walk is not None:
            # pedalling: thighs pump around the crank
            ph = walk * 0.8
            nhip = 52 + 16 * math.sin(ph)
            nkn = 86 - 22 * math.sin(ph + 0.9)
            fhip = 52 - 16 * math.sin(ph)
            fkn = 86 + 22 * math.sin(ph + 0.9)
        elif walk is not None:
            ph = walk
            sw = 24 * math.sin(ph)
            nhip, fhip = sw, -sw
            nkn = 8 + 26 * max(0.0, -math.sin(ph + 0.6))
            fkn = 8 + 26 * max(0.0, math.sin(ph + 0.6))
            bob = -1.6 * abs(math.cos(ph))
        pdy = p.get("pdy", 0) or 0
        seat = p.get("seat", 0) or 0
        floor = p.get("floor", 0) or 0
        pel_y = lerp(-leg + pdy, -46.0 * leg / 78.0, seat)      # seated on a stool (~46 cm for an adult)
        if floor > 0:                              # sitting on a mat / floor
            pel_y = lerp(-leg + pdy, -15.0, floor)
        elif cyc:                                  # on the cyclo saddle
            pel_y = -92.0
        elif (p.get("kneel", 0) or 0) > 0.5:        # kneeling upright on the knees
            pel_y = -leg * 0.5 - 4
        pel_y += bob
        pel = (0.0, pel_y)
        lean = p["torso"]
        breath_s = 1.0 + 0.012 * breath
        neck = (pel[0] + math.sin(ang(lean)) * tl, pel[1] - math.cos(ang(lean)) * tl * breath_s)
        J = dict(pel=pel, neck=neck, lean=lean)
        # hips
        hw = s["hip"]
        for side, dxh, hip_a, kn_a in (("n", -0.18 * hw, nhip, nkn), ("f", 0.16 * hw, fhip, fkn)):
            H = (pel[0] + dxh, pel[1] + 3)
            d1 = self.limb_dir(hip_a)
            K = (H[0] + d1[0] * thigh, H[1] + d1[1] * thigh)
            d2 = self.limb_dir(hip_a - kn_a)
            A = (K[0] + d2[0] * shin, K[1] + d2[1] * shin)
            if pdy is None or p.get("nkn", 0) > 120:
                pass
            J[side + "hip"], J[side + "knee"], J[side + "ank"] = H, K, A
        # shoulders
        sw_ = s["shoulder"]
        up = (math.sin(ang(lean)), -math.cos(ang(lean)))
        rt = (math.cos(ang(lean)), math.sin(ang(lean)))
        def at_torso(fx, fy):   # fx across (+ = front), fy down from neck
            return (neck[0] + rt[0] * fx - up[0] * fy, neck[1] + rt[1] * fx - up[1] * fy)
        J["at_torso"] = at_torso
        J["nsh"] = at_torso(-0.30 * sw_, 5.5)
        J["fsh"] = at_torso(0.26 * sw_, 5.0)
        # head
        ht = p["head"] + lean * 0.4
        J["head_ang"] = lean + p["head"]
        hc_off = rot_pt(r * 0.12, -r * 0.92 - 4.5, ang(lean * 0.6 + p["head"] * 0.3))
        J["head"] = (neck[0] + hc_off[0], neck[1] + hc_off[1])
        return J

    def head_point(self, J, lx, ly):
        a = ang(J["head_ang"])
        q = rot_pt(lx, ly, a)
        return (J["head"][0] + q[0], J["head"][1] + q[1])

    def arm_points(self, J, p, side, t=0.0, walk=None):
        s = self.s
        a, b = s["arm_up"], s["arm_lo"]
        S = J[side + "sh"]
        tgt = p.get("ik_" + side)
        if tgt:
            r = s["head_r"]
            at = J["at_torso"]
            T = {
              "mouth": self.head_point(J, r * 0.55, r * 0.62),
              "mouth_side": self.head_point(J, r * 0.2, r * 0.55),
              "face": self.head_point(J, r * 0.35 if side == "n" else r * 0.75, r * 0.2),
              "ear_n": self.head_point(J, -r * 0.55, r * 0.1),
              "ear_f": self.head_point(J, r * 0.35, r * 0.05),
              "chest_c": at(s["shoulder"] * 0.42, 20),
              "chest_n": at(s["shoulder"] * 0.18, 17),
              "chest_f": at(s["shoulder"] * 0.30, 22),
              "cross_n": at(s["shoulder"] * 0.30, 24),
              "hug_n": at(s["shoulder"] * 0.30, 30),
              "hug_f": at(s["shoulder"] * 0.45, 34),
              "cross_f": at(s["shoulder"] * 0.05, 22),
              "book_n": at(s["shoulder"] * 0.75, 34),
              "book_f": at(s["shoulder"] * 1.0, 32),
              "belly": at(s["shoulder"] * 0.55 + s["belly"], s["torso_len"] * 0.72),
              "shoulder_top": at(s["shoulder"] * 0.05, -9),
              "shoulder_top2": at(s["shoulder"] * 0.3, -7),
              "knee": (J["nknee"][0] - 3, J["nknee"][1] - 7),
              "knee_f": (J["fknee"][0] - 1, J["fknee"][1] - 7),
            }[tgt]
            if tgt in ("chest_c", "cross_n", "cross_f", "book_n", "book_f", "chest_n", "chest_f", "hug_n", "hug_f"):
                bend = -1
            else:
                bend = -1
            E, W = self.ik(S, T, a, b, bend=bend)
            return S, E, W
        sh, el = p[side + "sh"], p[side + "el"]
        anim = p.get("anim")
        if walk is not None and not p.get("hold"):
            sw = 20 * math.sin(walk)
            sh = sh + (-sw if side == "n" else sw)
        if anim == "wave" and side == "n":
            el += 18 * math.sin(t * 9)
        if anim == "write" and side == "f":
            el += 5 * math.sin(t * 13) ; sh += 2.5 * math.sin(t * 7.3)
        if anim == "work":
            sh += 8 * math.sin(t * 5 + (0 if side == "n" else 2))
        if anim == "hoe":
            sw_ = math.sin(t * 2.6)
            sh += 34 * max(-0.3, sw_)
            el -= 10 * max(0, sw_)
        if anim == "work_small":
            el += 6 * math.sin(t * 4 + (0 if side == "n" else 1.5))
        if anim == "shake":
            sh += 1.2 * math.sin(t * 23 + (0 if side == "n" else 1))
        if anim == "sweep":
            sh += 14 * math.sin(t * 3.2)
        if anim == "stir":
            sh += 10 * math.sin(t * 2.4 + (0 if side == "n" else 0.4))
            el += 8 * math.cos(t * 2.4)
        sh += p["torso"] * 0.0
        d1 = self.limb_dir(sh + J["lean"] * 0.5)
        E = (S[0] + d1[0] * a, S[1] + d1[1] * a)
        d2 = self.limb_dir(sh + el + J["lean"] * 0.5)
        W = (E[0] + d2[0] * b, E[1] + d2[1] * b)
        return S, E, W

    # ------------------------------------------------------------ drawing
    def draw(self, canvas, zoom, x, y, st):
        """st: dict(pose=dict, facing=+1/-1, scale, t, blink, look=(dx,dy), expr=dict, mouth=(shape, amt),
        walk=phase or None, breath, tint=None, alpha)"""
        s = self.s
        if s.get("animal"):
            return self.draw_animal(canvas, zoom, x, y, st)
        g = Ctx(canvas, zoom * st.get("scale", 1.0))
        p = st["pose"]
        facing = st.get("facing", 1)
        if p.get("turn"):
            facing = -facing
        canvas.save()
        canvas.translate(x, y)
        sc = st.get("scale", 1.0)
        canvas.scale(sc * facing, sc)
        if p.get("lie"):
            if p.get("bed"):
                canvas.translate(0, -64)
                canvas.rotate(-82)
            else:
                canvas.translate(0, -12)
                canvas.rotate(-90)
        J = self.skeleton(p, st.get("t", 0), st.get("breath", 0), st.get("walk"))
        t = st.get("t", 0.0)
        arms = {sd: self.arm_points(J, p, sd, t, st.get("walk")) for sd in ("n", "f")}
        # ground shadow
        if not p.get("lie") and st.get("shadow", True):
            sh = skia.Paint(AntiAlias=True, Color=rgb("#2a1a10", 60))
            canvas.drawOval(skia.Rect.MakeLTRB(-s["hip"] * 0.95, -3.5, s["hip"] * 1.05, 3.5), sh)
        if "cape" in s["extras"] and not p.get("lie"):
            self.draw_cape(g, J, p, st)
        self.draw_arm(g, J, arms["f"], "f", p)
        self.draw_legs(g, J, p, st)
        self.draw_torso(g, J, p, st)
        self.draw_head(g, J, p, st)
        self.draw_arm(g, J, arms["n"], "n", p)
        self.draw_props(g, J, p, arms, st)
        canvas.restore()
        return J

    # arms ---------------------------------------------------------------------
    def draw_arm(self, g, J, pts, side, p):
        s = self.s
        S, E, W = pts
        far = side == "f"
        skin = shade(s["skin"], 0.12) if far else s["skin"]
        shirt = shade(s["shirt"], 0.14) if far else s["shirt"]
        aw = s["arm_w"] * (0.94 if far else 1.0)
        style = s["shirt_style"]
        g.limb([S, E, W], aw, skin)
        # sleeve
        if style in ("short", "short_collar", "short_open", "work_rolled", "uniform_short", "tunic"):
            f = 0.62 if style != "work_rolled" else 0.95
            Ms = (S[0] + (E[0] - S[0]) * f, S[1] + (E[1] - S[1]) * f)
            if style == "work_rolled":
                g.limb([S, E], aw + 2.4, shirt)
                cuff = (E[0] + (W[0] - E[0]) * 0.12, E[1] + (W[1] - E[1]) * 0.12)
                g.limb([E, cuff], aw + 3.2, shade(shirt, 0.1))
            else:
                g.limb([S, Ms], aw + 1.4, shirt)
                hx0 = (S[0] + (E[0] - S[0]) * (f - 0.06), S[1] + (E[1] - S[1]) * (f - 0.06))
                g.limb([hx0, Ms], aw + 1.4, shade(shirt, 0.08), cap=skia.Paint.kButt_Cap)
        elif style in ("jacket", "uniform", "blouse_long", "mandarin", "coat"):
            cuff = (E[0] + (W[0] - E[0]) * 0.9, E[1] + (W[1] - E[1]) * 0.9)
            g.limb([S, E, cuff], aw + 2.4, shirt)
            if style == "jacket":
                g.limb([cuff, (cuff[0] + (W[0] - E[0]) * 0.06, cuff[1] + (W[1] - E[1]) * 0.06)], aw + 1.2,
                       s["shirt2"])
        elif style == "blouse":
            Ms = (S[0] + (E[0] - S[0]) * 0.75, S[1] + (E[1] - S[1]) * 0.75)
            g.limb([S, Ms], aw + 2.2, shirt)
        elif style == "singlet":
            pass
        ex_ = s["extras"]
        def seg(A, B, f0, f1):
            return [(A[0] + (B[0] - A[0]) * f0, A[1] + (B[1] - A[1]) * f0),
                    (A[0] + (B[0] - A[0]) * f1, A[1] + (B[1] - A[1]) * f1)]
        gold = shade(GOLD, 0.12) if far else GOLD
        if "armbands_gold" in ex_:
            g.limb(seg(S, E, 0.42, 0.56), aw + 2.0, gold, cap=skia.Paint.kButt_Cap)
        if "arm_guards" in ex_:
            g.limb(seg(E, W, 0.3, 0.9), aw + 2.6, gold, cap=skia.Paint.kButt_Cap)
            g.line(seg(E, W, 0.34, 0.86), color=shade(gold, 0.3), w=g.lw() * 0.7)
        if "bangles" in ex_:
            g.limb(seg(E, W, 0.84, 0.93), aw + 1.6, gold, cap=skia.Paint.kButt_Cap)
        if "bracelet_thread" in ex_ and not far:
            g.limb(seg(E, W, 0.88, 0.93), aw + 1.0, "#b3312c", cap=skia.Paint.kButt_Cap)
        if "watch" in s["extras"] and not far:
            wp = (E[0] + (W[0] - E[0]) * 0.95, E[1] + (W[1] - E[1]) * 0.95)
            g.limb([wp, (wp[0] + (W[0] - E[0]) * 0.035, wp[1] + (W[1] - E[1]) * 0.035)], aw * 0.55, "#c9a13a",
                   cap=skia.Paint.kButt_Cap)
        self.draw_hand(g, E, W, p.get(side + "hand", "open"), skin, far)

    def draw_hand(self, g, E, W, kind, skin, far):
        s = self.s
        r = s["arm_w"] * 0.6
        dx, dy = W[0] - E[0], W[1] - E[1]
        L = math.hypot(dx, dy) or 1
        ux, uy = dx / L, dy / L
        a = math.degrees(math.atan2(uy, ux))
        c = g.c
        c.save()
        c.translate(W[0] + ux * r * 0.55, W[1] + uy * r * 0.55)
        c.rotate(a)
        # local: +x along the forearm direction, +y is the "palm/thumb" side
        if kind == "fist":
            g.ellipse(0.2 * r, 0, r * 0.95, r * 0.85, skin)
            g.line([(0.55 * r, -0.35 * r), (0.6 * r, 0.35 * r)], w=g.lw() * 0.7)
        elif kind == "point":
            g.ellipse(0.1 * r, 0, r * 0.9, r * 0.82, skin)
            finger = rrect(0.4 * r, -0.62 * r, 1.55 * r, 0.52 * r, 0.26 * r)
            g.shape(finger, skin)
        elif kind == "point_up":
            g.ellipse(0.1 * r, 0, r * 0.9, r * 0.82, skin)
            c.save(); c.rotate(-80)
            g.shape(rrect(0.2 * r, -0.26 * r, 1.4 * r, 0.52 * r, 0.26 * r), skin)
            c.restore()
        elif kind in ("flat", "flat_up"):
            pth = smooth([(-0.3 * r, -0.55 * r), (0.9 * r, -0.62 * r), (1.75 * r, -0.3 * r), (1.85 * r, 0.15 * r),
                          (1.2 * r, 0.55 * r), (-0.3 * r, 0.55 * r)])
            if kind == "flat_up":
                c.rotate(-70)
            g.shape(pth, skin)
            g.line([(0.95 * r, -0.2 * r), (1.55 * r, -0.1 * r)], w=g.lw() * 0.6)
        else:  # open
            pth = smooth([(-0.35 * r, -0.62 * r), (0.8 * r, -0.72 * r), (1.55 * r, -0.4 * r), (1.62 * r, 0.25 * r),
                          (1.0 * r, 0.62 * r), (-0.35 * r, 0.6 * r)])
            g.shape(pth, skin)
            thumb = smooth([(0.2 * r, 0.35 * r), (0.9 * r, 0.62 * r), (1.15 * r, 1.0 * r), (0.8 * r, 1.08 * r),
                            (0.25 * r, 0.8 * r)])
            g.shape(thumb, skin)
            g.line([(0.95 * r, -0.28 * r), (1.45 * r, -0.2 * r)], w=g.lw() * 0.6)
            g.line([(0.95 * r, 0.05 * r), (1.45 * r, 0.12 * r)], w=g.lw() * 0.6)
        c.restore()

    # legs ---------------------------------------------------------------------
    def draw_legs(self, g, J, p, st):
        s = self.s
        lw = s["leg_w"]
        style = s["pants_style"]
        seated = (p.get("seat", 0) or 0) > 0.5
        if style == "skirt" and not p.get("lie"):
            # feet first then the sampot tube over the legs
            for side in ("f", "n"):
                self.draw_foot(g, J[side + "ank"], side, p, st)
            pel = J["pel"]
            hw = s["hip"]
            if seated or (p.get("kneel", 0) or 0) > 0.5:
                kn = J["nknee"]
                pth = smooth([(pel[0] - hw * 0.55, pel[1] - 4), (pel[0] + hw * 0.5, pel[1] - 5),
                              (kn[0] + 6, kn[1] - 4), (kn[0] + 7, kn[1] + 8), (pel[0] - hw * 0.45, pel[1] + 10)])
                g.shape(pth, s["skirt"])
                if not (p.get("kneel", 0) or 0) > 0.5:
                    a1, a2 = J["nank"], J["fank"]
                    g.shape(poly([(kn[0] - 6, kn[1]), (kn[0] + 7, kn[1]), (a1[0] + 7, a1[1] - 5),
                                  (a1[0] - 7, a1[1] - 5)]), s["skirt"])
            else:
                a1, a2 = J["nank"], J["fank"]
                bot = max(a1[1], a2[1]) - 6
                xl = min(a1[0], a2[0]) - 9
                xr = max(a1[0], a2[0]) + 9
                pth = smooth([(pel[0] - hw * 0.52, pel[1] - 6), (pel[0] + hw * 0.52, pel[1] - 6),
                              (pel[0] + hw * 0.56, pel[1] + 20), (xr, bot), (xl, bot),
                              (pel[0] - hw * 0.56, pel[1] + 20)], tension=0.35)
                g.shape(pth, s["skirt"])
                # woven stripes
                c = g.c
                c.save(); c.clipPath(pth, skia.ClipOp.kIntersect, True)
                ns = s.get("skirt_stripes", 6)
                if ns == 1:        # one woven band near the hem
                    g.line([(xl - 20, bot - 7), (xr + 20, bot - 5)], color=s["skirt2"], w=3.4)
                else:
                    for i in range(ns):
                        yy = pel[1] + 8 + i * (bot - pel[1] - 8) / ns
                        g.line([(xl - 20, yy), (xr + 20, yy + 2)], color=s["skirt2"], w=2.0)
                c.restore()
                g.c.drawPath(pth, g.stroke(OUTLINE, g.lw()))
            return
        pants = s["pants"]
        for side in ("f", "n"):
            H, K, A = J[side + "hip"], J[side + "knee"], J[side + "ank"]
            far = side == "f"
            col = shade(pants, 0.14) if far else pants
            skin = shade(s["skin"], 0.12) if far else s["skin"]
            if style == "cropped":
                cut = (K[0] + (A[0] - K[0]) * 0.55, K[1] + (A[1] - K[1]) * 0.55)
                g.limb([K, A], lw * 0.62, skin)
                g.limb([H, K, cut], lw * 1.22, col, cap=skia.Paint.kButt_Cap)
                g.limb([(cut[0] - (A[0] - K[0]) * 0.08, cut[1] - (A[1] - K[1]) * 0.08), cut], lw * 1.3,
                       shade(col, 0.1), cap=skia.Paint.kButt_Cap)
                g.circle(H[0], H[1], lw * 0.6, col, outline=False)
            elif style == "rolled":
                cut = (K[0] + (A[0] - K[0]) * 0.45, K[1] + (A[1] - K[1]) * 0.45)
                g.limb([K, A], lw * 0.6, skin)
                g.limb([H, K, cut], lw, col, cap=skia.Paint.kButt_Cap)
                g.limb([(cut[0] - (A[0] - K[0]) * 0.07, cut[1] - (A[1] - K[1]) * 0.07), cut], lw + 1.4,
                       light(col, 0.12), cap=skia.Paint.kButt_Cap)
                g.circle(H[0], H[1], lw * 0.5, col, outline=False)
            elif style == "shorts":
                cut = (H[0] + (K[0] - H[0]) * 0.8, H[1] + (K[1] - H[1]) * 0.8)
                g.limb([K, A], lw * 0.62, skin)
                g.limb([cut, K], lw * 0.66, skin)
                g.limb([H, cut], lw + 1, col)
            else:
                # stop the trouser tube half a width above the ankle so its round end sits on the shoe
                vx, vy = A[0] - K[0], A[1] - K[1]
                L = math.hypot(vx, vy) or 1
                A2 = (A[0] - vx / L * lw * 0.45, A[1] - vy / L * lw * 0.45)
                g.limb([H, K, A2], lw, col)
            if "shin_guards" in s["extras"]:
                gold = shade(GOLD, 0.12) if far else GOLD
                q0 = (K[0] + (A[0] - K[0]) * 0.2, K[1] + (A[1] - K[1]) * 0.2)
                q1 = (K[0] + (A[0] - K[0]) * 0.78, K[1] + (A[1] - K[1]) * 0.78)
                g.limb([q0, q1], lw * 1.05, gold, cap=skia.Paint.kButt_Cap)
                g.line([q0, q1], color=shade(gold, 0.3), w=g.lw() * 0.7)
            self.draw_foot(g, A, side, p, st)
        # hips/seat block joins legs to torso
        pel = J["pel"]
        hw = s["hip"]
        if seated:
            g.shape(smooth([(pel[0] - hw * 0.42, pel[1] - 6), (pel[0] + hw * 0.4, pel[1] - 6),
                            (pel[0] + hw * 0.38, pel[1] + 8), (pel[0] - hw * 0.4, pel[1] + 8)], tension=0.3),
                    pants)

    def draw_foot(self, g, A, side, p, st):
        s = self.s
        far = side == "f"
        skin = shade(s["skin"], 0.12) if far else s["skin"]
        fl = s["leg_w"] * 1.55
        x, y = A
        kind = s["shoes"]
        if kind == "shoe":
            col = shade(s["shoe_col"], 0.1) if far else s["shoe_col"]
            pth = smooth([(x - fl * 0.28, y - 5.5), (x + fl * 0.45, y - 5), (x + fl * 0.78, y - 1.5),
                          (x + fl * 0.7, y + 1.5), (x - fl * 0.3, y + 1.5)], tension=0.4)
            g.shape(pth, col)
            g.line([(x + fl * 0.1, y - 4.4), (x + fl * 0.3, y - 4.6)], color=light(col, 0.4), w=g.lw() * 0.8)
        else:
            pth = smooth([(x - fl * 0.25, y - 5), (x + fl * 0.4, y - 3.8), (x + fl * 0.72, y - 1.2),
                          (x + fl * 0.66, y + 0.8), (x - fl * 0.28, y + 0.8)], tension=0.4)
            if kind == "sandal":
                g.shape(rrect(x - fl * 0.32, y - 0.2, fl * 1.08, 2.0, 1.0), s["shoe_col"])
            g.shape(pth, skin)
            if kind == "sandal":
                g.line([(x + fl * 0.35, y - 3.6), (x + fl * 0.05, y - 1.0), (x - fl * 0.1, y - 4.0)],
                       color=s["shoe_col"], w=1.8)

    # torso --------------------------------------------------------------------
    def torso_path(self, J, extra=0.0):
        s = self.s
        at = J["at_torso"]
        sw, ww, hw, tl = s["shoulder"], s["waist"], s["hip"], s["torso_len"]
        bl = s["belly"]
        hem = tl + (8 if s["shirt_style"] in ("short_open", "work_rolled", "singlet", "blouse", "blouse_long", "tunic")
                    else (34 if s["shirt_style"] == "coat" else 2))
        pts = [at(-0.5 * sw, 6), at(-0.3 * sw, -0.5), at(0.0, -2.0), at(0.3 * sw, -0.8), at(0.5 * sw, 6),
               at(0.48 * sw + bl * 0.3, tl * 0.38), at(0.42 * ww + bl, tl * 0.7), at(0.47 * hw + bl * 0.4, hem),
               at(0.0, hem + 1), at(-0.5 * hw, hem), at(-0.44 * ww, tl * 0.66), at(-0.5 * sw, tl * 0.3)]
        return smooth(pts, tension=0.45)

    def draw_torso(self, g, J, p, st):
        s = self.s
        at = J["at_torso"]
        sw, tl = s["shoulder"], s["torso_len"]
        style = s["shirt_style"]
        shirt = s["shirt"]
        body = self.torso_path(J)
        # neck
        r = s["head_r"]
        n0 = at(0.05 * sw, 2)
        g.limb([n0, (J["neck"][0] + 1.5, J["neck"][1] - 7)], r * 0.62, s["skin"])
        g.shape(body, shirt)
        c = g.c
        # cel shadow on the back side
        c.save(); c.clipPath(body, skia.ClipOp.kIntersect, True)
        sh = smooth([at(-0.6 * sw, -2), at(-0.28 * sw, 6), at(-0.2 * sw, tl * 0.6), at(-0.3 * sw, tl + 6),
                     at(-0.8 * sw, tl + 6)])
        c.drawPath(sh, g.fill(shade(shirt, 0.16)))
        if style == "singlet":
            pass
        if style == "strapless":       # bare shoulders above a wrapped top
            c.drawPath(smooth([at(-0.7 * sw, -6), at(0.7 * sw, -6), at(0.7 * sw, 9), at(0.0, 11), at(-0.7 * sw, 8)],
                              tension=0.3), g.fill(s["skin"]))
        if style == "armor":           # gold breastplate: shaded bands + a big central ornament
            for fy in (tl * 0.45, tl * 0.62):
                g.line([at(-0.55 * sw, fy), at(0.55 * sw, fy + 1)], color=shade(shirt, 0.3), w=g.lw() * 0.8)
        c.restore()
        g.c.drawPath(body, g.stroke(OUTLINE, g.lw()))
        if style == "strapless":
            g.limb([at(-0.46 * sw, 9), at(0.0, 11), at(0.46 * sw, 9)], 3.2, GOLD)
            q = at(0.18 * sw, 13)
            g.shape(poly([(q[0], q[1] - 3.2), (q[0] + 3, q[1]), (q[0], q[1] + 3.6), (q[0] - 3, q[1])]), GOLD)
        if style == "armor":
            q = at(0.12 * sw, tl * 0.3)
            g.shape(poly([(q[0], q[1] - 9), (q[0] + 8, q[1]), (q[0], q[1] + 10), (q[0] - 8, q[1])]), light(shirt, 0.15))
            g.circle(q[0], q[1], 2.6, "#9e2a2a")
        if style in ("short_collar", "short", "short_open", "work_rolled", "uniform"):
            # placket + buttons
            g.line([at(0.2 * sw, 4), at(0.24 * sw, tl - 2)], color=shade(shirt, 0.25), w=g.lw() * 0.8)
            for i in range(4):
                bx = at(0.25 * sw, 10 + i * (tl - 14) / 4)
                g.circle(bx[0], bx[1], 0.9, shade(shirt, 0.35), outline=False)
            # collar
            col2 = light(shirt, 0.18)
            g.shape(poly([at(-0.05 * sw, -1), at(0.2 * sw, 7), at(0.3 * sw, -1.5)]), col2)
            g.shape(poly([at(0.12 * sw, -1.5), at(0.22 * sw, 7), at(0.38 * sw, 1)]), col2)
            if style == "short_open":
                g.shape(poly([at(0.13 * sw, 0), at(0.23 * sw, 10), at(0.32 * sw, 0)]), s["shirt2"])
            if style in ("uniform",):
                for fx in (-0.18, 0.3):
                    pk = at(fx * sw, 12)
                    g.shape(rrect(pk[0] - 4, pk[1], 8, 7, 1), shade(shirt, 0.08))
        elif style == "jacket":
            # white shirt V + tie + lapels
            v = poly([at(0.02 * sw, -1), at(0.22 * sw, tl * 0.5), at(0.42 * sw, -0.5)])
            g.shape(v, s["shirt2"])
            if "tie" in s["extras"]:
                g.shape(poly([at(0.2 * sw, 3), at(0.26 * sw, 3), at(0.3 * sw, tl * 0.45), at(0.23 * sw, tl * 0.52),
                              at(0.18 * sw, tl * 0.45)]), "#6b2a22")
            g.shape(poly([at(0.0 * sw, -1), at(0.18 * sw, tl * 0.5), at(0.1 * sw, tl * 0.2)]), light(shirt, 0.1))
            g.shape(poly([at(0.44 * sw, 0), at(0.26 * sw, tl * 0.52), at(0.42 * sw, tl * 0.25)]), light(shirt, 0.1))
            for i in range(2):
                bx = at(0.27 * sw, tl * 0.62 + i * 8)
                g.circle(bx[0], bx[1], 1.1, shade(shirt, 0.4), outline=False)
            pk = at(-0.1 * sw, tl * 0.2)
            g.line([pk, (pk[0] + 9, pk[1])], color=shade(shirt, 0.3), w=g.lw() * 0.8)
        elif style in ("blouse", "blouse_long"):
            g.line([at(0.02 * sw, 0), at(0.2 * sw, 6), at(0.4 * sw, 0.5)], color=shade(shirt, 0.3), w=g.lw())
        elif style == "singlet":
            g.shape(smooth([at(-0.25 * sw, -0.5), at(0.2 * sw, 9), at(0.42 * sw, 0)], close=False),
                    s["skin"], outline=True)
        elif style == "mandarin":
            g.shape(rrect(at(0.02 * sw, -3)[0] - 1, at(0, -3)[1] - 1, sw * 0.42, 5, 2), light(shirt, 0.1))
            g.line([at(0.25 * sw, 2), at(0.27 * sw, tl - 1)], color=shade(shirt, 0.25), w=g.lw() * 0.8)
            for i in range(5):
                bx = at(0.27 * sw, 5 + i * (tl - 8) / 5)
                g.circle(bx[0], bx[1], 1.0, "#c9a44a", outline=False)
        elif style == "coat":
            v = poly([at(0.04 * sw, -1), at(0.24 * sw, tl * 0.42), at(0.42 * sw, -0.5)])
            g.shape(v, s["shirt2"])
            g.line([at(0.24 * sw, tl * 0.42), at(0.26 * sw, tl + 30)], color=shade(shirt, 0.25), w=g.lw() * 0.9)
            pk = at(0.05 * sw, tl * 0.75)
            g.shape(rrect(pk[0] - 6, pk[1], 12, 9, 1.5), shade(shirt, 0.06))
        if "tie_navy" in s["extras"]:
            g.shape(poly([at(0.2 * sw, 3), at(0.26 * sw, 3), at(0.3 * sw, tl * 0.45), at(0.23 * sw, tl * 0.52),
                          at(0.18 * sw, tl * 0.45)]), "#23324f")
        if "patches" in s["extras"]:
            for (fx, fy) in ((-0.15, 18), (0.2, 38)):
                q = at(fx * sw, fy)
                g.shape(rrect(q[0] - 4, q[1] - 4, 8, 7, 0.8), shade(shirt, 0.3), olw=g.lw() * 0.6)
        if "necklace" in s["extras"]:
            g.line([at(-0.05 * sw, 0), at(0.2 * sw, 7), at(0.4 * sw, 0.5)], color="#d4a93c", w=g.lw() * 0.9)
        if "whistle" in s["extras"]:
            g.line([at(0.3 * sw, 0), at(0.36 * sw, 14)], color="#d9d0b8", w=g.lw() * 0.7)
            q = at(0.36 * sw, 15); g.circle(q[0], q[1], 1.6, "#c0c4c8")
        if "pocket_pen" in s["extras"]:
            q = at(-0.1 * sw, 11)
            g.shape(rrect(q[0] - 5, q[1], 10, 8, 1), shade(shirt, 0.08), olw=g.lw() * 0.6)
            g.line([(q[0] - 1, q[1] - 3), (q[0] - 1, q[1] + 3)], color="#23324f", w=1.4)
        if "stethoscope" in s["extras"]:
            g.line([at(-0.2 * sw, 0), at(-0.12 * sw, 16), at(0.1 * sw, 20)], color="#2a2a2e", w=g.lw() * 0.9)
            q = at(0.1 * sw, 21); g.circle(q[0], q[1], 2.2, "#b8bcc0")
        if "medal" in s["extras"]:
            q = at(-0.1 * sw, 14)
            g.shape(poly([(q[0] - 2, q[1] - 4), (q[0] + 2, q[1] - 4), (q[0] + 1, q[1]), (q[0] - 1, q[1])]), "#7a1f1a")
            g.circle(q[0], q[1] + 2.5, 2.6, "#d4a93c")
        # belt / waist
        if style not in ("blouse", "blouse_long", "coat", "mandarin") and s["pants_style"] != "skirt":
            bcol = "#2a1a12" if "belt_black" in s["extras"] else ("#6b4226" if "belt" in s["extras"] else None)
            if style == "jacket":
                bcol = None
            if bcol:
                b1, b2 = at(-0.5 * s["hip"], tl - 1), at(0.48 * s["hip"] + s["belly"] * 0.4, tl - 1)
                g.limb([b1, b2], 3.2, bcol)
                bk = at(0.3 * s["hip"], tl - 1)
                g.shape(rrect(bk[0] - 2.2, bk[1] - 2.2, 4.4, 4.4, 0.8), "#c9a44a")
        if "grease" in s["extras"]:
            for (fx, fy, rr) in ((0.1, 30, 3), (-0.2, 40, 2.2), (0.3, 20, 1.6)):
                q = at(fx * sw, fy)
                g.circle(q[0], q[1], rr, shade(shirt, 0.45), outline=False, alpha=150)
        if "epaulettes" in s["extras"]:
            for fx in (-0.4, 0.38):
                q = at(fx * sw, 1.5)
                g.shape(rrect(q[0] - 4.5, q[1] - 1.6, 9, 3.2, 1.2), "#7a1f1a")
        if style == "tunic":
            g.line([at(-0.05 * sw, 0), at(0.2 * sw, 9), at(0.42 * sw, 0.5)], color=shade(shirt, 0.3), w=g.lw())
            g.line([at(0.2 * sw, 9), at(0.26 * sw, tl * 0.55)], color=shade(shirt, 0.2), w=g.lw() * 0.7)
        ex_ = s["extras"]
        if "chest_medallion" in ex_:
            g.line([at(0.34 * sw, 0), at(0.0, tl * 0.45), at(-0.46 * s["hip"], tl - 4)], color="#6b4226", w=2.6)
            q = at(0.14 * sw, tl * 0.3)
            g.shape(poly([(q[0], q[1] - 5.5), (q[0] + 5, q[1]), (q[0], q[1] + 6), (q[0] - 5, q[1])]), GOLD)
        if "shoulder_guards" in ex_:
            big = 1.3 if style == "armor" else 1.0
            for fx, far_ in ((-0.4, False), (0.34, True)):
                q = at(fx * sw, 2.5)
                col = shade(GOLD, 0.14) if far_ else GOLD
                g.shape(smooth([(q[0] - 7 * big, q[1] + 1), (q[0] - 4 * big, q[1] - 4 * big), (q[0] + 5 * big, q[1] - 4 * big),
                                (q[0] + 8 * big, q[1] + 2), (q[0] + 4 * big, q[1] + 6 * big), (q[0] - 5 * big, q[1] + 6 * big)],
                               tension=0.4), col)
                g.line([(q[0] - 5 * big, q[1] + 2), (q[0] + 6 * big, q[1] + 2)], color=shade(col, 0.3), w=g.lw() * 0.7)
        if "cape" in ex_:              # the cape's fold over the back shoulder
            cc = s.get("cape", "#9e2a2a")
            g.shape(smooth([at(-0.55 * sw, 8), at(-0.45 * sw, -2), at(-0.15 * sw, -3), at(-0.3 * sw, 10)], tension=0.4), cc)
        if "basket_hip" in ex_:
            self.draw_basket(g, J, st)
        if "robe_over" in s["extras"]:
            self.draw_robe(g, J, st)
        if "krama_neck" in s["extras"] or "krama_shoulder" in s["extras"]:
            self.draw_krama(g, J, st)
        if "sash_waist" in s["extras"]:
            self.draw_sash(g, J, st)
        if "front_panel" in ex_:
            hw = s["hip"]
            pan = poly([at(0.02 * hw, tl), at(0.42 * hw, tl), at(0.38 * hw, tl + 34), at(0.06 * hw, tl + 34)])
            g.shape(pan, "#e8d9b0")
            for k in range(3):
                q = at(0.22 * hw, tl + 8 + k * 9)
                g.shape(poly([(q[0], q[1] - 3), (q[0] + 3, q[1]), (q[0], q[1] + 3), (q[0] - 3, q[1])]), GOLD, olw=g.lw() * 0.6)
        if "gold_belt" in ex_:
            hw = s["hip"]
            b1, b2 = at(-0.52 * hw, tl - 1), at(0.5 * hw, tl - 1)
            g.limb([b1, b2], 3.6, GOLD)
            q = at(0.18 * hw, tl - 1)
            g.shape(poly([(q[0], q[1] - 5), (q[0] + 5, q[1]), (q[0], q[1] + 5), (q[0] - 5, q[1])]), light(GOLD, 0.15))
            g.circle(q[0], q[1], 1.5, "#9e2a2a", outline=False)
        if "sword_hip" in ex_:
            hw = s["hip"]
            h0 = at(-0.35 * hw, tl + 2)
            g.limb([h0, (h0[0] - 22, h0[1] + 30)], 4.2, "#2a1d16")
            g.line([(h0[0] - 20, h0[1] + 27), (h0[0] - 22, h0[1] + 30)], color=GOLD, w=4.6)
            g.limb([h0, (h0[0] + 6, h0[1] - 9)], 2.6, "#5a3a22")
            g.line([(h0[0] - 3, h0[1] + 2), (h0[0] + 3, h0[1] - 2)], color=GOLD, w=2.8)
        if "scarf_red" in s["extras"]:
            self.draw_scarf(g, J, st)
        if "shoulder_bag" in s["extras"]:
            self.draw_bag(g, J, st)
        if "rag_shoulder" in s["extras"]:
            q = at(-0.3 * sw, 2)
            g.shape(poly([(q[0] - 5, q[1] - 2), (q[0] + 4, q[1] - 3), (q[0] + 6, q[1] + 16), (q[0] - 2, q[1] + 18)]),
                    "#c9c1a8")

    def draw_cape(self, g, J, p, st):
        """a long cape hanging behind the body from the shoulders; optional high collar (villain)."""
        s = self.s
        at = J["at_torso"]
        sw, tl = s["shoulder"], s["torso_len"]
        col = s.get("cape", "#9e2a2a")
        t = st.get("t", 0)
        wind = st.get("wind", 0.0)
        sway = (2 + 8 * wind) * math.sin(t * (1.6 + 2 * wind))
        low = 0.0 if not (p.get("seat") or p.get("kneel")) else -0.45
        L = tl + s["leg_len"] * (0.82 + low)
        pts = [at(-0.52 * sw, 2), at(0.3 * sw, 1), at(0.1 * sw, tl * 0.6),
               at(0.05 * sw + sway * 0.3, L), at(-0.62 * sw - 10 * wind + sway, L + 2),
               at(-0.6 * sw - 6 * wind + sway * 0.6, tl * 0.5)]
        cape = smooth([(x_, min(y_, -2.0)) for x_, y_ in pts], tension=0.35)   # never below the ground
        g.shape(cape, shade(col, 0.18))
        g.line([at(-0.3 * sw, tl * 0.4), at(-0.35 * sw + sway * 0.6, L - 4)], color=shade(col, 0.35), w=g.lw() * 0.8)
        if "cape_collar" in s["extras"]:
            n = J["neck"]
            r = s["head_r"]
            g.shape(poly([(n[0] - r * 0.9, n[1] + 6), (n[0] - r * 1.25, n[1] - r * 1.25), (n[0] - r * 0.2, n[1] - r * 0.3),
                          (n[0] + r * 0.2, n[1] + 4)]), col)

    def draw_basket(self, g, J, st):
        """a woven bamboo basket of greens resting on the front hip."""
        s = self.s
        at = J["at_torso"]
        tl, hw = s["torso_len"], s["hip"]
        b = at(0.62 * hw + 4, tl + 2)
        k = tl / 52.0
        for i, dx in enumerate((-6, 0, 6)):
            g.circle(b[0] + dx * k, b[1] - 7 * k, 4.2 * k, ("#5f9a4a", "#6fae55", "#548a40")[i])
        bowl = smooth([(b[0] - 12 * k, b[1] - 6 * k), (b[0] + 12 * k, b[1] - 6 * k), (b[0] + 9 * k, b[1] + 7 * k),
                       (b[0] - 9 * k, b[1] + 7 * k)], tension=0.35)
        g.shape(bowl, "#b88a4a")
        g.c.save(); g.c.clipPath(bowl, skia.ClipOp.kIntersect, True)
        for i in range(-3, 4):
            g.line([(b[0] + i * 4 * k, b[1] - 7 * k), (b[0] + i * 3 * k, b[1] + 8 * k)], color="#8f6532", w=g.lw() * 0.6)
        g.c.restore()
        g.limb([(b[0] - 12 * k, b[1] - 6 * k), (b[0] + 12 * k, b[1] - 6 * k)], 2.2, "#a0773c")

    # animals ------------------------------------------------------------------
    # A spec with animal="dog" | "monkey" | "elephant" is drawn by these instead of the human rig.
    # They face screen-right, stand on the ground line, blink, lip-sync (open mouth), wag / sway and walk.
    def animal_skeleton(self, t=0.0, walk=None):
        kind = self.s["animal"]
        bob = -1.2 * abs(math.sin(walk)) if walk is not None else 0.0
        if kind == "monkey" and walk is not None:
            bob = -4.0 * abs(math.sin(walk))
        head = {"dog": (20, -44), "monkey": (2, -40), "elephant": (27, -52)}[kind]
        neck = {"dog": (13, -33), "monkey": (2, -29), "elephant": (18, -44)}[kind]
        pel = {"dog": (-10, -24), "monkey": (0, -12), "elephant": (-12, -34)}[kind]
        J = dict(head=(head[0], head[1] + bob), neck=(neck[0], neck[1] + bob), pel=(pel[0], pel[1] + bob),
                 lean=0.0, head_ang=0.0, bob=bob)
        J["at_torso"] = lambda fx, fy: (neck[0] + fx, neck[1] + bob + fy)
        return J

    def draw_animal(self, canvas, zoom, x, y, st):
        s = self.s
        sc = st.get("scale", 1.0)
        g = Ctx(canvas, zoom * sc)
        facing = st.get("facing", 1)
        if st["pose"].get("turn"):
            facing = -facing
        canvas.save()
        canvas.translate(x, y)
        canvas.scale(sc * facing, sc)
        J = self.animal_skeleton(st.get("t", 0), st.get("walk"))
        if st.get("shadow", True):
            w = {"dog": 26, "monkey": 16, "elephant": 36}[s["animal"]]
            canvas.drawOval(skia.Rect.MakeLTRB(-w, -3, w, 3), skia.Paint(AntiAlias=True, Color=rgb("#2a1a10", 60)))
        getattr(self, "_draw_" + s["animal"])(g, J, st)
        canvas.restore()
        return J

    def _animal_eye(self, g, cx, cy, rr, st, iris=None):
        ex = st.get("expr") or EXPR["neutral"]
        eo = ex["eo"] * (1 - st.get("blink", 0.0))
        if eo < 0.12:
            g.line([(cx - rr, cy), (cx, cy + rr * 0.35), (cx + rr, cy)], w=g.lw() * 1.3)
            return
        lx, ly = st.get("look", (0.35, 0.0))
        g.ellipse(cx, cy, rr, rr * min(1.15, 0.35 + eo * 0.8), "#1a0d06")
        if iris:
            g.circle(cx + lx * rr * 0.2, cy + rr * 0.1, rr * 0.62, iris, outline=False)
            g.circle(cx + lx * rr * 0.2, cy + rr * 0.1, rr * 0.34, "#1a0d06", outline=False)
        g.circle(cx - rr * 0.32 + lx * rr * 0.15, cy - rr * 0.35, rr * 0.34, "#ffffff", outline=False)
        g.circle(cx + rr * 0.3, cy + rr * 0.35, rr * 0.13, "#ffffff", outline=False)

    def _animal_mouth(self, g, cx, cy, w, st, tongue=True):
        """closed smile, or an open happy/talking mouth (uses the lip-sync amount)."""
        ex = st.get("expr") or EXPR["neutral"]
        shape, amt = st.get("mouth", (None, 0.0))
        if shape in (None, "closed") or amt < 0.05:
            amt = 0.8 if ex.get("mouth") in ("smile", "surprisedO") or ex["mc"] > 0.4 else 0.0
        if amt < 0.05:
            curve = 0.35 * w * max(-0.6, min(1.0, ex["mc"] + 0.4))
            g.line([(cx - w, cy - curve * 0.3), (cx, cy + curve), (cx + w, cy - curve * 0.3)], w=g.lw() * 1.1)
            return
        h = w * (0.5 + 0.7 * amt)
        m = smooth([(cx - w, cy - 1), (cx + w, cy - 1), (cx + w * 0.5, cy + h), (cx - w * 0.5, cy + h)], tension=0.5)
        g.shape(m, "#5a1f1c")
        if tongue:
            g.c.save(); g.c.clipPath(m, skia.ClipOp.kIntersect, True)
            g.ellipse(cx, cy + h * 0.95, w * 0.6, h * 0.5, "#e07a7a", outline=False)
            g.c.restore()

    def _draw_dog(self, g, J, st):
        s = self.s
        t, walk, bob = st.get("t", 0), st.get("walk"), J["bob"]
        white, tan = s["skin"], s["hair"]
        for i, (lx, far) in enumerate(((-6, True), (15, True), (-13, False), (9, False))):
            a = 22 * math.sin(walk + (0 if i % 3 == 0 else math.pi)) if walk is not None else 0
            dx = math.sin(math.radians(a)) * 17
            col = shade(white, 0.14) if far else white
            g.limb([(lx, -22 + bob), (lx + dx, -2)], 6.8, col)
            g.ellipse(lx + dx + 1.5, -2, 4.4, 2.6, col)
        wag = math.sin(t * 9) * 12
        g.limb([(-19, -28 + bob), (-26, -36 + bob), (-27 + wag * 0.4, -46 + bob)], 4.6, tan)
        body = skia.Path(); body.addOval(skia.Rect.MakeLTRB(-22, -35 + bob, 20, -14 + bob))
        g.c.drawPath(body, g.fill(white))
        g.c.save(); g.c.clipPath(body, skia.ClipOp.kIntersect, True)
        g.ellipse(-8, -34 + bob, 12, 8, tan, outline=False)
        g.c.restore()
        g.c.drawPath(body, g.stroke(OUTLINE, g.lw()))
        g.limb([(10, -38 + bob), (16, -29 + bob)], 4.2, "#b3312c")      # red collar + gold tag
        g.circle(15, -26.5 + bob, 1.9, GOLD)
        hx, hy = J["head"]
        g.c.save(); g.c.translate(hx, hy); g.c.rotate(4 * math.sin(t * 1.3))
        g.ellipse(-6, -2, 5, 9, shade(tan, 0.12), rot=18)                 # far ear
        g.ellipse(0, 0, 12.5, 11.5, white)
        g.ellipse(9, 5, 7.5, 5.8, white)                                  # snout
        g.ellipse(15.5, 2.6, 2.4, 1.8, "#1a120e")                         # nose
        self._animal_eye(g, 3.5, -3, 2.9, st)
        self._animal_eye(g, 10.5, -3.4, 2.2, st)
        self._animal_mouth(g, 11, 8.2, 3.6, st)
        g.shape(smooth([(-9, -9), (-3, -10), (-2, 2), (-6, 12), (-12, 9), (-12, -2)], tension=0.45), tan)  # near ear
        g.c.restore()

    def _draw_monkey(self, g, J, st):
        s = self.s
        t, bob = st.get("t", 0), J["bob"]
        fur, face = s["hair"], s["skin"]
        sway = math.sin(t * 1.7) * 3
        g.limb([(-9, -8 + bob), (-15, -9 + bob), (-18, -17 + bob), (-15 + sway, -24 + bob), (-11 + sway, -21 + bob)],
               3.4, fur)                                                  # curled tail
        g.limb([(4, -26 + bob), (10, -16 + bob), (12, -6 + bob)], 4.2, shade(fur, 0.14))   # far arm
        g.ellipse(0, -18 + bob, 11, 13.5, fur)                            # body
        g.ellipse(3, -16 + bob, 6.5, 9.5, face, outline=False)            # belly
        g.ellipse(-3, -6 + bob, 10, 6, fur)                               # haunches
        g.ellipse(7, -1.5, 5, 2.4, face)                                  # feet
        g.ellipse(-8, -1.5, 5, 2.4, shade(face, 0.1))
        hx, hy = J["head"]
        g.c.save(); g.c.translate(hx, hy); g.c.rotate(3 * math.sin(t * 1.1))
        for ex_, far in ((-10, False), (9.5, True)):
            g.circle(ex_, -1, 4.6, shade(fur, 0.1) if far else fur)
            g.circle(ex_, -1, 2.6, face, outline=False)
        g.circle(0, 0, 11, fur)
        g.shape(smooth([(-4, -6), (2, -2.5), (9, -6), (11, 2), (6, 9), (-2, 9), (-6, 2)], tension=0.5), face)
        self._animal_eye(g, 1.5, -2.5, 2.5, st)
        self._animal_eye(g, 7.5, -2.5, 2.1, st)
        g.circle(4.5, 2.3, 0.7, "#3a2217", outline=False); g.circle(6.2, 2.3, 0.7, "#3a2217", outline=False)
        self._animal_mouth(g, 4.5, 5.2, 3.4, st, tongue=False)
        g.c.restore()
        g.limb([(2, -26 + bob), (8, -15 + bob), (9, -6 + bob)], 4.2, fur)  # near arm
        g.circle(9.5, -5 + bob, 2.4, face)

    def _draw_elephant(self, g, J, st):
        s = self.s
        t, walk, bob = st.get("t", 0), st.get("walk"), J["bob"]
        gray = s["skin"]
        for i, (lx, far) in enumerate(((-9, True), (17, True), (-18, False), (9, False))):
            a = 14 * math.sin(walk + (0 if i % 3 == 0 else math.pi)) if walk is not None else 0
            dx = math.sin(math.radians(a)) * 20
            col = shade(gray, 0.14) if far else gray
            g.limb([(lx, -26 + bob), (lx + dx, -4)], 11.5, col, cap=skia.Paint.kButt_Cap)
            g.shape(rrect(lx + dx - 6.4, -6, 12.8, 6, 2.5), col)
            for k in (-2.6, 0.4, 3.4):
                g.circle(lx + dx + k, -2.2, 1.0, "#e9e4dc", outline=False)
        g.limb([(-27, -40 + bob), (-31, -26 + bob)], 1.8, shade(gray, 0.2))  # tail
        g.circle(-31, -25 + bob, 1.8, "#4a4f55", outline=False)
        g.ellipse(-2, -36 + bob, 28, 18, gray)                            # body
        hx, hy = J["head"]
        flap = 1 + 0.07 * math.sin(t * 2.1)
        sway = math.sin(t * 1.8) * 5
        g.c.save(); g.c.translate(hx, hy)
        g.limb([(12, 6), (17, 16), (18 + sway * 0.5, 26), (22 + sway, 29)], 7.6, gray)   # trunk
        g.c.save(); g.c.translate(-9, 1); g.c.scale(flap, 1)
        g.ellipse(0, 0, 13, 16, gray)                                     # ear
        g.ellipse(0.5, 0.5, 9, 12, "#e9a8b8", outline=False)
        g.c.restore()
        g.circle(4, -2, 16, gray)
        g.ellipse(3, 11, 11, 6, gray, outline=False)
        g.c.drawPath(smooth([(-11, 5), (0, 13), (13, 9)], close=False), g.stroke(OUTLINE, g.lw()))
        g.shape(poly([(4, -21), (10, -15), (4, -9), (-2, -15)]), GOLD)    # gold forehead ornament
        g.circle(4, -15, 1.8, "#9e2a2a", outline=False)
        self._animal_eye(g, 7, -3, 3.3, st, iris=s["eye"])
        self._animal_eye(g, 15, -3.2, 2.5, st, iris=s["eye"])
        self._animal_mouth(g, 11, 11.5, 3.2, st, tongue=True)
        g.c.drawOval(skia.Rect.MakeLTRB(1, 4, 8, 8), skia.Paint(AntiAlias=True, Color=rgb("#e98a9a", 90)))
        g.c.restore()

    def draw_sash(self, g, J, st):
        """a red waist sash tied at the front with two tails that sway in the breeze."""
        s = self.s
        at = J["at_torso"]
        tl, hw, sw = s["torso_len"], s["hip"], s["shoulder"]
        col = s.get("sash", "#b3312c")
        t = st.get("t", 0)
        wind = st.get("wind", 0.0)
        band = smooth([at(-0.52 * hw, tl - 7), at(0.0, tl - 8), at(0.5 * hw, tl - 6), at(0.5 * hw, tl + 2),
                       at(0.0, tl + 1), at(-0.52 * hw, tl + 1)], tension=0.35)
        g.shape(band, col)
        g.line([at(-0.45 * hw, tl - 3), at(0.45 * hw, tl - 2)], color=shade(col, 0.25), w=g.lw() * 0.6)
        kx = 0.3 * hw
        ks = tl / 52.0
        for k, (ln, ph) in enumerate(((22 * ks, 0.0), (17 * ks, 1.3))):
            sway = (2.0 + 4.0 * wind) * math.sin(t * (2.2 + 2.5 * wind) + ph) - 6 * wind
            p0 = at(kx - 2 + k * 4, tl - 2)
            sway *= ks
            tail = poly([(p0[0] - 2.6, p0[1]), (p0[0] + 2.6, p0[1]),
                         (p0[0] + 3 + sway * 0.6 + k * 3, p0[1] + ln), (p0[0] - 2 + sway + k * 3, p0[1] + ln + 1)])
            g.shape(tail, shade(col, 0.06 * k))
        q = at(kx, tl - 3)
        g.shape(smooth([(q[0] - 4, q[1] - 3), (q[0] + 4, q[1] - 3.5), (q[0] + 4.5, q[1] + 3), (q[0] - 3.5, q[1] + 3.5)]),
                light(col, 0.08))

    def draw_scarf(self, g, J, st):
        """a plain red scarf knotted at the neck, one end fluttering."""
        s = self.s
        at = J["at_torso"]
        sw = s["shoulder"]
        col = s.get("sash", "#b3312c")
        t = st.get("t", 0)
        wind = st.get("wind", 0.0)
        ring = smooth([at(-0.4 * sw, 4), at(-0.1 * sw, -3.5), at(0.25 * sw, -3), at(0.45 * sw, 3), at(0.22 * sw, 9),
                       at(-0.12 * sw, 8)])
        g.shape(ring, col)
        g.line([at(-0.25 * sw, 3), at(0.3 * sw, 4)], color=shade(col, 0.25), w=g.lw() * 0.6)
        ks = s["torso_len"] / 52.0
        sway = (1.5 + 5 * wind) * math.sin(t * (2.0 + 3 * wind)) * ks
        p0 = at(0.28 * sw, 6)
        tail = poly([(p0[0] - 2.5, p0[1]), (p0[0] + 3, p0[1] - 1),
                     (p0[0] + (4 + sway * 0.5 - 12 * wind) * ks, p0[1] + (11 - 5 * wind) * ks),
                     (p0[0] + (-1 + sway - 14 * wind) * ks, p0[1] + (12 - 6 * wind) * ks)])
        g.shape(tail, shade(col, 0.05))

    def draw_bag(self, g, J, st):
        """a small brown shoulder bag: strap across the chest, bag resting on the back hip."""
        s = self.s
        at = J["at_torso"]
        sw, tl, hw = s["shoulder"], s["torso_len"], s["hip"]
        col = s.get("bag", "#7a4e2c")
        g.line([at(0.3 * sw, 1), at(0.0, tl * 0.5), at(-0.48 * hw, tl + 2)], color=shade(col, 0.15), w=2.4)
        k = tl / 52.0
        b = at(-0.62 * hw, tl + 3)
        bag = smooth([(b[0] - 9 * k, b[1] - 6 * k), (b[0] + 8 * k, b[1] - 7 * k), (b[0] + 9 * k, b[1] + 9 * k),
                      (b[0] - 8 * k, b[1] + 10 * k)], tension=0.3)
        g.shape(bag, col)
        g.shape(smooth([(b[0] - 9 * k, b[1] - 6 * k), (b[0] + 8 * k, b[1] - 7 * k), (b[0] + 7 * k, b[1] + 1 * k),
                        (b[0] - 8 * k, b[1] + 2 * k)], tension=0.3), light(col, 0.1))
        g.circle(b[0], b[1] + 1.5 * k, 1.3 * k, "#c9a44a", outline=False)

    def draw_robe(self, g, J, st):
        """an open brown over-robe with gold trim (the old teacher)."""
        s = self.s
        at = J["at_torso"]
        sw, tl, hw = s["shoulder"], s["torso_len"], s["hip"]
        col = s.get("robe", "#7a5534")
        gold = "#c9a44a"
        back = smooth([at(-0.52 * sw, 4), at(-0.1 * sw, -2), at(0.08 * sw, 6), at(0.02 * sw, tl + 40),
                       at(-0.58 * hw, tl + 42), at(-0.55 * sw, tl * 0.4)], tension=0.35)
        g.shape(back, col)
        front = poly([at(0.26 * sw, -1), at(0.5 * sw, 5), at(0.52 * hw, tl + 40), at(0.34 * sw, tl + 41)])
        g.shape(front, shade(col, 0.05))
        g.line([at(0.08 * sw, 6), at(0.02 * sw, tl + 40)], color=gold, w=g.lw() * 1.4)
        g.line([at(0.26 * sw, -1), at(0.34 * sw, tl + 41)], color=gold, w=g.lw() * 1.4)

    def draw_krama(self, g, J, st):
        s = self.s
        at = J["at_torso"]
        sw = s["shoulder"]
        c1, c2 = s["krama"]
        t = st.get("t", 0)
        sway = 1.4 * math.sin(t * 2.1)
        if "krama_neck" in s["extras"]:
            ring = smooth([at(-0.36 * sw, 3), at(-0.1 * sw, -3), at(0.25 * sw, -2.5), at(0.42 * sw, 3),
                           at(0.22 * sw, 8), at(-0.1 * sw, 7)])
            tail = poly([at(0.12 * sw, 5), at(0.3 * sw, 5), at(0.3 * sw + sway * 0.3, 30), at(0.14 * sw + sway * 0.3, 32)])
            parts = [ring, tail]
        else:
            band = poly([at(-0.4 * sw, 0), at(-0.15 * sw, -3), at(0.46 * sw, s["torso_len"] * 0.6),
                         at(0.3 * sw, s["torso_len"] * 0.72)])
            parts = [band]
        for pth in parts:
            g.shape(pth, c1)
            c = g.c
            c.save(); c.clipPath(pth, skia.ClipOp.kIntersect, True)
            bb = pth.getBounds()
            step = 3.2
            yy = bb.top()
            i = 0
            while yy < bb.bottom():
                g.line([(bb.left(), yy), (bb.right(), yy)], color=c2, w=1.1, alpha=190)
                yy += step; i += 1
            xx = bb.left()
            while xx < bb.right():
                g.line([(xx, bb.top()), (xx, bb.bottom())], color=c2, w=1.1, alpha=190)
                xx += step
            c.restore()
            g.c.drawPath(pth, g.stroke(OUTLINE, g.lw()))

    # head ---------------------------------------------------------------------
    def draw_head(self, g, J, p, st):
        s = self.s
        c = g.c
        r = s["head_r"]
        wx = s["head_wx"]
        hx, hy = J["head"]
        c.save()
        c.translate(hx, hy)
        c.rotate(J["head_ang"])
        ex = st.get("expr") or EXPR["neutral"]
        self.draw_hair(g, r, "back", st)
        # head shape
        jw = s["jaw"]
        head = smooth([(0.0, -r * 1.0), (r * 0.72 * wx, -r * 0.78), (r * 0.98 * wx, -r * 0.18),
                       (r * 0.95 * wx, r * 0.35), (r * (0.7 + 0.08 * jw) * wx, r * 0.86), (r * 0.3, r * 1.02),
                       (-r * (0.28 + 0.15 * jw), r * 0.9), (-r * 0.82, r * 0.35), (-r * 0.95, -r * 0.25),
                       (-r * 0.7, -r * 0.8)], tension=0.5)
        skin = s["skin"]
        if s["weak"] > 0:
            skin = mix(skin, "#d8c7b0", s["weak"] * 0.35)
        c.drawPath(head, g.fill(skin))
        c.save(); c.clipPath(head, skia.ClipOp.kIntersect, True)
        c.drawPath(smooth([(-r * 1.2, -r), (-r * 0.55, -r * 0.2), (-r * 0.45, r * 0.6), (-r * 0.1, r * 1.3),
                           (-r * 1.3, r * 1.3)]), g.fill(shade(skin, 0.13)))
        c.restore()
        c.save(); c.clipPath(head, skia.ClipOp.kIntersect, True)
        kp = skia.Paint(AntiAlias=True)
        kp.setShader(skia.GradientShader.MakeRadial(skia.Point(r * 0.45, -r * 0.35), r * 0.9,
                                                    [rgb(light(skin, 0.3), 110), rgb(light(skin, 0.3), 0)]))
        c.drawCircle(r * 0.45, -r * 0.35, r * 0.9, kp)
        c.restore()
        c.drawPath(head, g.stroke(OUTLINE, g.lw()))
        # ear
        g.ellipse(-r * 0.46, r * 0.1, r * 0.16, r * 0.25, skin)
        g.line([(-r * 0.43, -r * 0.02), (-r * 0.5, r * 0.12), (-r * 0.42, r * 0.22)], w=g.lw() * 0.7)
        # blush
        if s["blush"] > 0:
            bp = skia.Paint(AntiAlias=True, Color=rgb("#e06a5a", int(255 * s["blush"] * 0.7)))
            bp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.08))
            c.drawOval(skia.Rect.MakeLTRB(r * 0.08, r * 0.28, r * 0.42, r * 0.5), bp)
            c.drawOval(skia.Rect.MakeLTRB(r * 0.72, r * 0.28, r * 0.9, r * 0.48), bp)
        self.draw_facial_hair(g, r)
        self.draw_eyes(g, r, ex, st)
        # nose
        # small rounded 3/4 nose between the eyes, pointing toward the facing side
        nose_sh = smooth([(r * 0.4 * wx, r * 0.18), (r * 0.52 * wx, r * 0.28), (r * 0.5 * wx, r * 0.36),
                          (r * 0.38 * wx, r * 0.36), (r * 0.34 * wx, r * 0.3)], tension=0.45)
        g.c.drawPath(nose_sh, g.fill(shade(skin, 0.12), 120))
        g.line([(r * 0.47 * wx, r * 0.2), (r * 0.54 * wx, r * 0.31), (r * 0.47 * wx, r * 0.36),
                (r * 0.38 * wx, r * 0.35)], w=g.lw() * 0.85)
        g.circle(r * 0.44 * wx, r * 0.335, r * 0.022, shade(skin, 0.45), outline=False)
        self.draw_mouth(g, r, ex, st)
        if s["age"] > 0.3:
            a = int(160 * min(1, s["age"]))
            g.line([(r * 0.66, r * 0.38), (r * 0.58, r * 0.62)], w=g.lw() * 0.6, alpha=a)
            g.line([(r * 0.0, -r * 0.62), (r * 0.25, -r * 0.64)], w=g.lw() * 0.5, alpha=int(a * 0.7))
        self.draw_hair(g, r, "front", st)
        if "flower_hair" in s["extras"]:
            fx, fy = -r * 0.62, -r * 0.78
            for k in range(5):
                a = k * 2 * math.pi / 5 - 0.3
                g.circle(fx + math.cos(a) * r * 0.13, fy + math.sin(a) * r * 0.13, r * 0.12, "#fbf7ee")
            g.circle(fx, fy, r * 0.07, "#f2c53d", outline=False)
        if "headwrap_krama" in s["extras"]:
            self.draw_headwrap(g, r, st)
        self.draw_brows(g, r, ex, st)
        if "crown_gold" in s["extras"]:
            tiers = poly([(-r * 0.78, -r * 0.95), (-r * 0.5, -r * 1.5), (-r * 0.2, -r * 1.35), (0.0, -r * 2.3),
                          (r * 0.2, -r * 1.35), (r * 0.5, -r * 1.5), (r * 0.78, -r * 0.98)])
            g.shape(tiers, GOLD)
            for k in range(3):
                yy = -r * (1.25 + k * 0.28)
                g.line([(-r * (0.45 - k * 0.12), yy), (r * (0.45 - k * 0.12), yy)], color=shade(GOLD, 0.3), w=g.lw() * 0.7)
            base = smooth([(-r * 0.95, -r * 0.62), (0, -r * 0.9), (r * 0.95, -r * 0.66), (r * 0.9, -r * 0.92),
                           (0, -r * 1.12), (-r * 0.9, -r * 0.9)], tension=0.35)
            g.shape(base, light(GOLD, 0.12))
            g.circle(0, -r * 0.9, r * 0.1, "#9e2a2a")
        if "tiara_gold" in s["extras"]:
            g.shape(poly([(-r * 0.7, -r * 0.88), (-r * 0.45, -r * 1.22), (-r * 0.2, -r * 1.02), (0.05, -r * 1.48),
                          (r * 0.3, -r * 1.02), (r * 0.52, -r * 1.2), (r * 0.72, -r * 0.84), (0.0, -r * 1.0)]), GOLD)
            g.circle(r * 0.05, -r * 1.1, r * 0.07, "#9e2a2a", outline=False)
        if "earrings_drop" in s["extras"]:
            g.circle(-r * 0.46, r * 0.38, r * 0.06, GOLD)
            g.shape(poly([(-r * 0.46, r * 0.42), (-r * 0.38, r * 0.62), (-r * 0.46, r * 0.72), (-r * 0.54, r * 0.62)]), GOLD,
                    olw=g.lw() * 0.6)
        if "headband_red" in s["extras"]:
            band = smooth([(-r * 0.98, -r * 0.35), (0, -r * 0.62), (r * 0.96, -r * 0.42), (r * 0.94, -r * 0.24),
                           (0, -r * 0.44), (-r * 0.98, -r * 0.16)], tension=0.4)
            g.shape(band, "#b3312c")
            g.shape(poly([(-r * 0.95, -r * 0.3), (-r * 1.35, -r * 0.05), (-r * 1.25, r * 0.12), (-r * 0.9, -r * 0.18)]),
                    "#9a2a26")
        if "cap_police" in s["extras"]:
            crown = smooth([(-r * 0.95, -r * 0.35), (-r * 0.8, -r * 1.18), (r * 0.6, -r * 1.25), (r * 0.98, -r * 0.5),
                            (r * 0.9, -r * 0.38)], tension=0.4)
            g.shape(crown, "#a88f55")
            g.shape(rrect(-r * 0.97, -r * 0.5, r * 1.9, r * 0.2, r * 0.05), "#3a2a1a")
            g.shape(smooth([(r * 0.55, -r * 0.34), (r * 1.35, -r * 0.3), (r * 1.3, -r * 0.2), (r * 0.5, -r * 0.2)],
                           tension=0.3), "#2a1d12")
            g.circle(r * 0.28, -r * 0.72, r * 0.12, "#d4a93c")
        if "cap_guard" in s["extras"]:
            crown = smooth([(-r * 0.95, -r * 0.4), (-r * 0.85, -r * 1.05), (r * 0.6, -r * 1.1), (r * 0.98, -r * 0.5),
                            (r * 0.9, -r * 0.4)], tension=0.4)
            g.shape(crown, "#4f5838")
            g.shape(smooth([(r * 0.55, -r * 0.42), (r * 1.3, -r * 0.36), (r * 1.25, -r * 0.26), (r * 0.5, -r * 0.28)],
                           tension=0.3), "#2e3320")
        if "headband_white" in s["extras"]:
            band = smooth([(-r * 0.98, -r * 0.35), (0, -r * 0.62), (r * 0.96, -r * 0.42), (r * 0.94, -r * 0.24),
                           (0, -r * 0.44), (-r * 0.98, -r * 0.16)], tension=0.4)
            g.shape(band, "#ece6d8")
        if "glasses" in s["extras"]:
            for (cx, rx) in ((r * 0.05, r * 0.27), (r * 0.64, r * 0.21)):
                g.c.drawOval(skia.Rect.MakeLTRB(cx - rx, -r * 0.3, cx + rx, r * 0.2), g.stroke("#2a1d14", g.lw() * 0.9))
            g.line([(r * 0.32, -r * 0.1), (r * 0.43, -r * 0.1)], color="#2a1d14", w=g.lw() * 0.9)
            g.line([(-r * 0.22, -r * 0.08), (-r * 0.5, -r * 0.02)], color="#2a1d14", w=g.lw() * 0.9)
        if "earrings" in s["extras"]:
            g.circle(-r * 0.46, r * 0.4, r * 0.07, "#d4a93c")
        if "scar" in s["extras"]:
            g.line([(r * 0.72, r * 0.1), (r * 0.9, r * 0.36)], color=shade(s["skin"], 0.35), w=g.lw() * 0.9)
        c.restore()

    def draw_headwrap(self, g, r, st):
        """a checked krama tied round the head, knot and short tail at the back."""
        s = self.s
        c1, c2 = s["krama"]
        wrap = smooth([(-r * 1.02, -r * 0.2), (-r * 0.9, -r * 0.88), (-r * 0.2, -r * 1.2), (r * 0.6, -r * 1.05),
                       (r * 0.98, -r * 0.55), (r * 0.8, -r * 0.5), (r * 0.2, -r * 0.62), (-r * 0.45, -r * 0.45),
                       (-r * 0.8, -r * 0.05)], tension=0.45)
        tail = poly([(-r * 0.95, -r * 0.45), (-r * 1.35, -r * 0.1 + math.sin(st.get("t", 0) * 2) * r * 0.05),
                     (-r * 1.3, r * 0.35), (-r * 1.0, r * 0.05)])
        c = g.c
        for pth in (tail, wrap):
            c.drawPath(pth, g.fill(c1))
            c.save(); c.clipPath(pth, skia.ClipOp.kIntersect, True)
            bb = pth.getBounds()
            step = r * 0.2
            yy = bb.top()
            while yy < bb.bottom():
                g.line([(bb.left(), yy), (bb.right(), yy)], color=c2, w=r * 0.07, alpha=200); yy += step
            xx = bb.left()
            while xx < bb.right():
                g.line([(xx, bb.top()), (xx, bb.bottom())], color=c2, w=r * 0.07, alpha=200); xx += step
            c.restore()
            c.drawPath(pth, g.stroke(OUTLINE, g.lw()))
        g.circle(-r * 0.95, -r * 0.4, r * 0.17, shade(c1, 0.1))

    def draw_eyes(self, g, r, ex, st):
        s = self.s
        es = s["eye_scale"]
        blink = st.get("blink", 0.0)
        eo = ex["eo"] * (1 - blink)
        if s["weak"] > 0:
            eo *= 1 - s["weak"] * 0.25
        lx, ly = st.get("look", (0.35, 0.0))
        for (cx, cy, rx, ry) in ((r * 0.05, -r * 0.03, r * 0.2 * es, r * 0.25 * es),
                                 (r * 0.63, -r * 0.04, r * 0.15 * es, r * 0.24 * es)):
            c = g.c
            eye = skia.Path(); eye.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry))
            if eo < 0.08:
                g.line([(cx - rx, cy + ry * 0.1), (cx, cy + ry * 0.35), (cx + rx, cy + ry * 0.1)],
                       w=g.lw() * 1.25)
                continue
            c.drawPath(eye, g.fill("#fbf7f0"))
            c.save(); c.clipPath(eye, skia.ClipOp.kIntersect, True)
            ir = min(rx * 0.92, ry * 0.8)
            ix, iy = cx + lx * rx * 0.45, cy + ly * ry * 0.35 + ry * 0.08
            c.drawCircle(ix, iy, ir, g.fill(s["eye"]))
            c.drawCircle(ix, iy, ir * 0.55, g.fill("#1a0d06"))
            c.drawCircle(ix - ir * 0.35, iy - ir * 0.4, ir * 0.3, g.fill("#ffffff"))
            # lids
            top = cy - ry + 2 * ry * (1 - min(eo * 0.9, 1.0)) * 0.95
            lid = skia.Path(); lid.addRect(skia.Rect.MakeLTRB(cx - rx * 1.5, cy - ry * 1.6, cx + rx * 1.5, top))
            c.drawPath(lid, g.fill(s["skin"]))
            lo = ex.get("lo", 0.0)
            if lo > 0:
                bot = cy + ry - 2 * ry * lo * 0.5
                lid2 = skia.Path(); lid2.addRect(skia.Rect.MakeLTRB(cx - rx * 1.5, bot, cx + rx * 1.5, cy + ry * 1.6))
                c.drawPath(lid2, g.fill(s["skin"]))
            c.restore()
            # lash line / outline
            c.drawPath(eye, g.stroke(OUTLINE, g.lw() * 0.8))
            ty = max(top, cy - ry)
            g.line([(cx - rx * 1.05, ty + ry * 0.2), (cx, ty - ry * 0.05), (cx + rx * 1.05, ty + ry * 0.2)],
                   w=g.lw() * (1.6 if s["female"] else 1.25))
            if s["female"]:
                g.line([(cx + rx * 0.95, ty + ry * 0.12), (cx + rx * 1.35, ty - ry * 0.1)], w=g.lw())
            if s["bags"] > 0:
                g.line([(cx - rx * 0.7, cy + ry * 1.2), (cx + rx * 0.6, cy + ry * 1.25)], w=g.lw() * 0.55,
                       alpha=int(200 * s["bags"]))
            if ex.get("tears"):
                tp = skia.Paint(AntiAlias=True, Color=rgb("#9fd4f0", 220))
                c.drawOval(skia.Rect.MakeLTRB(cx - rx * 0.2, cy + ry * 1.1, cx + rx * 0.25, cy + ry * 1.65), tp)

    def draw_brows(self, g, r, ex, st):
        s = self.s
        bh = ex["bh"] * r
        ba = ex["ba"]
        col = s["hair"] if s["hair_style"] not in ("gray_bun",) else "#8e8a84"
        if s["hair_style"] == "topknot_white":
            col = "#d8d3ca"
        if s["hair_style"] == "bald_sides":
            col = "#2a211b"
        w = g.lw() * 3.0 * s["brow_w"]
        for (cx, cy, hw, inner_side) in ((r * 0.05, -r * 0.42, r * 0.24, +1), (r * 0.64, -r * 0.43, r * 0.17, -1)):
            cy -= bh
            # inner end is toward the nose-bridge (between the eyes, x ~ 0.35r)
            ia = math.radians(ba) * inner_side
            dy = math.tan(ia) * hw
            pts = [(cx - hw, cy + (dy if inner_side < 0 else -dy) * 0.5 + r * 0.02),
                   (cx, cy - r * 0.03), (cx + hw, cy + (-dy if inner_side < 0 else dy) * 0.5 + r * 0.02)]
            g.line(pts, color=col, w=w)

    def draw_mouth(self, g, r, ex, st):
        s = self.s
        shape, amt = st.get("mouth", (None, 0.0))
        mc = ex["mc"]
        cx, cy = r * 0.54, r * 0.6
        base_w = r * 0.44
        if shape is None or amt < 0.05:
            shape = ex.get("mouth", "closed")
            amt = 1.0 if shape not in ("closed", "smile") else 0.0
        w, h, rnd, teeth = MOUTHS[shape]
        hw = base_w * w * 0.5 * (1 - 0.25 * rnd * amt)
        hh = r * 0.22 * h * amt
        lift = -mc * r * 0.1
        if shape == "smile":
            lift = -r * 0.12
        if hh < r * 0.02:
            g.line([(cx - hw, cy + lift), (cx, cy + r * 0.02), (cx + hw * 0.9, cy + lift * 0.9)], w=g.lw() * 1.05)
            return
        top = cy - hh * 0.35
        bot = cy + hh * 0.65
        pth = smooth([(cx - hw, cy + lift * 0.6), (cx - hw * 0.4, top), (cx + hw * 0.45, top),
                      (cx + hw * 0.95, cy + lift * 0.6), (cx + hw * 0.4, bot), (cx - hw * 0.45, bot)], tension=0.55)
        c = g.c
        c.drawPath(pth, g.fill("#5a1f1c"))
        c.save(); c.clipPath(pth, skia.ClipOp.kIntersect, True)
        c.drawOval(skia.Rect.MakeLTRB(cx - hw * 0.6, bot - hh * 0.45, cx + hw * 0.6, bot + hh * 0.4), g.fill("#c46060"))
        if teeth:
            c.drawRect(skia.Rect.MakeLTRB(cx - hw, top - 2, cx + hw, top + hh * 0.22), g.fill("#f7f2ea"))
        c.restore()
        c.drawPath(pth, g.stroke(OUTLINE, g.lw() * 0.95))

    def draw_facial_hair(self, g, r):
        f = self.s["facial"]
        c = g.c
        if f == "stubble":
            p = skia.Paint(AntiAlias=True, Color=rgb("#3a3430", 34))
            pth = smooth([(r * 0.15, r * 0.4), (r * 0.9, r * 0.42), (r * 0.72, r * 0.9), (r * 0.3, r * 1.02),
                          (-r * 0.3, r * 0.85), (-r * 0.25, r * 0.5)])
            c.drawPath(pth, p)
            dp = skia.Paint(AntiAlias=True, Color=rgb("#2a221e", 70))
            import random
            rnd = random.Random(7)
            for _ in range(22):
                x = rnd.uniform(-r * 0.2, r * 0.85); y = rnd.uniform(r * 0.5, r * 0.95)
                c.drawCircle(x, y, r * 0.018, dp)
        elif f == "beard_white":
            pth = smooth([(r * 0.2, r * 0.55), (r * 0.62, r * 0.48), (r * 0.92, r * 0.55), (r * 0.7, r * 1.05),
                          (r * 0.45, r * 1.25), (r * 0.2, r * 1.0)], tension=0.45)
            g.shape(pth, "#e8e4dc")
        elif f == "beard_long":
            pth = smooth([(r * 0.1, r * 0.5), (r * 0.62, r * 0.46), (r * 0.98, r * 0.52), (r * 0.86, r * 1.1),
                          (r * 0.62, r * 1.9), (r * 0.45, r * 2.3), (r * 0.3, r * 1.7), (r * 0.02, r * 1.0)], tension=0.45)
            g.shape(pth, "#f1eee8")
            g.line([(r * 0.5, r * 1.0), (r * 0.48, r * 1.8)], color="#cfc9bf", w=g.lw() * 0.7)
            g.shape(smooth([(r * 0.28, r * 0.52), (r * 0.62, r * 0.4), (r * 0.96, r * 0.5), (r * 0.9, r * 0.6),
                            (r * 0.62, r * 0.54), (r * 0.32, r * 0.62)], tension=0.4), "#f7f5f0")
        elif f == "beard_full":      # short black beard round the jaw + moustache (king)
            col = self.s.get("beard", self.s["hair"])
            g.shape(smooth([(-r * 0.35, r * 0.2), (-r * 0.1, r * 0.72), (r * 0.25, r * 1.18), (r * 0.62, r * 1.22),
                            (r * 0.92, r * 0.85), (r * 0.9, r * 0.66), (r * 0.62, r * 0.82), (r * 0.3, r * 0.82),
                            (r * 0.05, r * 0.55), (-r * 0.2, r * 0.15)], tension=0.45), col)
            g.shape(smooth([(r * 0.26, r * 0.5), (r * 0.62, r * 0.4), (r * 0.94, r * 0.5), (r * 0.9, r * 0.6),
                            (r * 0.62, r * 0.52), (r * 0.3, r * 0.62)], tension=0.4), col)
        elif f == "goatee":          # pointed goatee + thin moustache (villain)
            col = self.s.get("beard", self.s["hair"])
            g.shape(poly([(r * 0.36, r * 0.82), (r * 0.72, r * 0.8), (r * 0.52, r * 1.45)]), col)
            g.shape(smooth([(r * 0.3, r * 0.52), (r * 0.62, r * 0.42), (r * 0.95, r * 0.5), (r * 1.05, r * 0.66),
                            (r * 0.9, r * 0.56), (r * 0.62, r * 0.5), (r * 0.36, r * 0.58)], tension=0.4), col, outline=False)
        elif f in ("mustache", "mustache_thin"):
            th = 0.09 if f == "mustache" else 0.05
            pth = smooth([(r * 0.3, r * 0.5), (r * 0.62, r * (0.46 - th)), (r * 0.9, r * 0.5), (r * 0.82, r * 0.56),
                          (r * 0.62, r * 0.52), (r * 0.36, r * 0.57)], tension=0.4)
            g.shape(pth, "#1e1714" if self.s["hair2"] is None else "#2b2622", outline=False)

    def draw_hair(self, g, r, layer, st):
        self._draw_hair(g, r, layer, st)
        s = self.s
        if layer == "front" and s["hair_style"] not in ("bald_sides", "boy_spiky"):
            hi = light(s["hair"], 0.35)
            g.line([(-r * 0.55, -r * 0.88), (-r * 0.25, -r * 1.0)], color=hi, w=g.lw() * 0.9, alpha=170)
            g.line([(r * 0.1, -r * 1.02), (r * 0.42, -r * 0.94)], color=hi, w=g.lw() * 0.7, alpha=140)

    def _draw_hair(self, g, r, layer, st):
        s = self.s
        hs = s["hair_style"]
        col = s["hair"]
        c = g.c
        hi = light(col, 0.22)
        if layer == "back":
            if hs == "bun":
                g.circle(-r * 0.78, -r * 0.05, r * 0.42, col)
            if hs == "gray_bun":
                g.circle(-r * 0.62, -r * 0.62, r * 0.38, col)
            if hs == "braids":
                for dx in (-r * 0.6, -r * 0.2):
                    g.limb([(dx, r * 0.2), (dx - r * 0.1, r * 0.9), (dx - r * 0.05, r * 1.5)], r * 0.22, col)
            if hs == "long_back":
                g.shape(smooth([(-r * 0.5, -r * 0.4), (-r * 1.05, r * 0.2), (-r * 1.0, r * 1.6), (-r * 0.75, r * 2.3),
                                (-r * 0.35, r * 2.0), (-r * 0.3, r * 0.6)], tension=0.45), col)
            if hs == "chignon_high":
                g.circle(-r * 0.4, -r * 1.02, r * 0.42, col)
                g.line([(-r * 0.75, -r * 1.05), (-r * 0.05, -r * 0.98)], color="#c9a44a", w=g.lw() * 1.4)
            if hs == "bun_top":
                g.circle(-r * 0.42, -r * 1.02, r * 0.4, col)
                g.line([(-r * 0.72, -r * 0.8), (-r * 0.12, -r * 0.86)], color="#d4a93c", w=g.lw() * 1.8)
            if hs == "topknot_black":
                g.circle(-r * 0.2, -r * 1.2, r * 0.34, col)
                g.line([(-r * 0.45, -r * 1.0), (r * 0.05, -r * 1.02)], color=GOLD, w=g.lw() * 1.4)
            if hs == "long_straight":
                g.shape(smooth([(-r * 0.4, -r * 0.6), (-r * 1.1, r * 0.1), (-r * 1.15, r * 2.4), (-r * 1.0, r * 4.4),
                                (-r * 0.2, r * 4.6), (r * 0.1, r * 3.2), (-r * 0.2, r * 0.9)], tension=0.45), col)
                g.line([(-r * 0.7, r * 1.0), (-r * 0.6, r * 4.0)], color=light(col, 0.18), w=g.lw() * 0.9)
            if hs == "spiky_tied":
                g.shape(poly([(-r * 0.2, -r * 0.9), (-r * 0.5, -r * 1.75), (-r * 0.55, -r * 1.25), (-r * 1.05, -r * 1.7),
                              (-r * 0.85, -r * 1.1), (-r * 1.4, -r * 1.2), (-r * 0.9, -r * 0.7)]), col)
            if hs == "topknot_white":
                g.shape(smooth([(-r * 0.5, -r * 0.5), (-r * 1.05, r * 0.1), (-r * 1.1, r * 1.3), (-r * 0.85, r * 1.9),
                                (-r * 0.45, r * 1.5), (-r * 0.35, r * 0.5)], tension=0.45), col)
                g.circle(-r * 0.15, -r * 1.18, r * 0.3, col)
                g.line([(-r * 0.4, -r * 1.0), (r * 0.1, -r * 1.02)], color="#c9a44a", w=g.lw() * 1.6)
            if hs in TIED_HAIR:
                g.shape(smooth([(-r * 1.02, -r * 0.1), (-r * 0.8, -r * 0.9), (0, -r * 1.13), (r * 0.8, -r * 0.85),
                                (r * 0.6, -r * 0.3), (-r * 0.9, r * 0.45)]), col)
            return
        # front layer (drawn over the face): hair cap
        if hs == "neat_side":
            cap = smooth([(-r * 0.98, r * 0.05), (-r * 0.98, -r * 0.62), (-r * 0.45, -r * 1.12), (r * 0.35, -r * 1.14),
                          (r * 0.92, -r * 0.72), (r * 0.98, -r * 0.42), (r * 0.62, -r * 0.6), (r * 0.15, -r * 0.55),
                          (-r * 0.2, -r * 0.5), (-r * 0.4, -r * 0.2), (-r * 0.62, r * 0.02)], tension=0.45)
            g.shape(cap, col)
            g.line([(-r * 0.3, -r * 1.02), (r * 0.2, -r * 0.8), (r * 0.7, -r * 0.7)], color=hi, w=g.lw() * 1.2)
        elif hs == "messy":
            cap = smooth([(-r * 0.98, r * 0.08), (-r * 1.02, -r * 0.6), (-r * 0.6, -r * 1.1), (-r * 0.2, -r * 1.2),
                          (r * 0.2, -r * 1.12), (r * 0.55, -r * 1.16), (r * 0.9, -r * 0.8), (r * 1.0, -r * 0.48),
                          (r * 0.7, -r * 0.58), (r * 0.45, -r * 0.46), (r * 0.1, -r * 0.6), (-r * 0.3, -r * 0.42),
                          (-r * 0.55, -r * 0.1), (-r * 0.66, r * 0.05)], tension=0.4)
            g.shape(cap, col)
            if s["hair2"]:
                g.shape(smooth([(-r * 0.66, r * 0.04), (-r * 0.98, r * 0.04), (-r * 0.95, -r * 0.35),
                                (-r * 0.6, -r * 0.3)], tension=0.4), s["hair2"], outline=False)
            g.line([(-r * 0.5, -r * 0.95), (0, -r * 0.9), (r * 0.5, -r * 0.95)], color=hi, w=g.lw())
        elif hs == "slick":
            cap = smooth([(-r * 0.98, r * 0.05), (-r * 1.0, -r * 0.6), (-r * 0.5, -r * 1.1), (r * 0.3, -r * 1.12),
                          (r * 0.82, -r * 0.82), (r * 0.8, -r * 0.7), (r * 0.3, -r * 0.8), (-r * 0.2, -r * 0.72),
                          (-r * 0.55, -r * 0.3), (-r * 0.66, r * 0.02)], tension=0.45)
            g.shape(cap, col)
            if s["hair2"]:
                g.shape(smooth([(-r * 0.66, r * 0.02), (-r * 0.97, r * 0.02), (-r * 0.98, -r * 0.4),
                                (-r * 0.58, -r * 0.35)], tension=0.4), s["hair2"], outline=False)
            for k in range(3):
                g.line([(-r * 0.7, -r * (0.5 + k * 0.18)), (r * 0.5, -r * (0.95 - k * 0.05))], color=hi, w=g.lw() * 0.8)
        elif hs == "boy_spiky":
            P_ = [(-1.0, 0.15), (-1.14, -0.25), (-1.0, -0.45), (-1.2, -0.82), (-0.86, -0.92), (-0.82, -1.34),
                  (-0.42, -1.12), (-0.18, -1.5), (0.1, -1.18), (0.48, -1.44), (0.62, -1.05), (1.08, -1.02),
                  (0.98, -0.72), (1.12, -0.5), (0.86, -0.46), (0.74, -0.2), (0.56, -0.44), (0.34, -0.2),
                  (0.2, -0.46), (-0.05, -0.28), (-0.2, -0.5), (-0.45, -0.3), (-0.58, -0.05), (-0.66, 0.1)]
            g.shape(smooth([(x * r, y * r) for x, y in P_], tension=0.34), col)
        elif hs in TIED_HAIR:
            cap = smooth([(-r * 0.98, r * 0.12), (-r * 1.0, -r * 0.6), (-r * 0.45, -r * 1.12), (r * 0.4, -r * 1.1),
                          (r * 0.92, -r * 0.62), (r * 0.9, -r * 0.44), (r * 0.4, -r * 0.62), (-r * 0.1, -r * 0.66),
                          (-r * 0.45, -r * 0.35), (-r * 0.62, r * 0.1)], tension=0.45)
            g.shape(cap, col)
            if hs == "braids":
                g.shape(smooth([(r * 0.1, -r * 0.7), (r * 0.9, -r * 0.62), (r * 0.9, -r * 0.35), (r * 0.5, -r * 0.4)],
                               tension=0.4), col)
            g.line([(-r * 0.6, -r * 0.8), (0, -r * 1.0), (r * 0.6, -r * 0.8)], color=hi, w=g.lw())
        elif hs in ("spiky", "spiky_tied"):
            pts = [(-r * 0.98, r * 0.05), (-r * 1.0, -r * 0.6)]
            for i in range(7):
                a = math.pi * (1.05 - i / 6 * 0.95)
                rr = r * (1.22 if i % 2 == 0 else 1.05)
                pts.append((math.cos(a) * rr * 0.95, -abs(math.sin(a)) * rr))
            pts += [(r * 0.95, -r * 0.5), (r * 0.5, -r * 0.6), (-r * 0.2, -r * 0.55), (-r * 0.6, r * 0.02)]
            g.shape(poly(pts), col)
        elif hs == "bald_sides":
            g.shape(smooth([(-r * 0.98, r * 0.12), (-r * 1.0, -r * 0.5), (-r * 0.75, -r * 0.8), (-r * 0.5, -r * 0.5),
                            (-r * 0.6, r * 0.12)], tension=0.4), col)
            g.line([(-r * 0.2, -r * 0.95), (r * 0.3, -r * 0.96)], color=light(s["skin"], 0.4), w=g.lw() * 1.4)
        elif hs == "wavy":
            pts = [(-r * 0.98, r * 0.1), (-r * 1.08, -r * 0.55), (-r * 0.8, -r * 1.0), (-r * 0.35, -r * 1.25),
                   (r * 0.1, -r * 1.18), (r * 0.5, -r * 1.25), (r * 0.95, -r * 0.9), (r * 1.02, -r * 0.5),
                   (r * 0.62, -r * 0.62), (r * 0.3, -r * 0.5), (-r * 0.1, -r * 0.62), (-r * 0.45, -r * 0.3),
                   (-r * 0.62, r * 0.05)]
            g.shape(smooth(pts, tension=0.5), col)
            g.line([(-r * 0.5, -r * 1.0), (-r * 0.1, -r * 0.9), (r * 0.4, -r * 1.02)], color=hi, w=g.lw())
        elif hs == "pompadour":
            cap = smooth([(-r * 0.98, r * 0.02), (-r * 1.0, -r * 0.62), (-r * 0.55, -r * 1.12), (r * 0.1, -r * 1.3),
                          (r * 0.75, -r * 1.25), (r * 1.02, -r * 0.8), (r * 0.9, -r * 0.55), (r * 0.4, -r * 0.66),
                          (-r * 0.3, -r * 0.55), (-r * 0.58, -r * 0.2), (-r * 0.64, r * 0.0)], tension=0.45)
            g.shape(cap, col)
            g.line([(-r * 0.2, -r * 1.1), (r * 0.5, -r * 1.15)], color=hi, w=g.lw() * 1.1)
        elif hs == "short":
            cap = smooth([(-r * 0.98, r * 0.02), (-r * 1.0, -r * 0.62), (-r * 0.5, -r * 1.1), (r * 0.35, -r * 1.1),
                          (r * 0.9, -r * 0.72), (r * 0.94, -r * 0.5), (r * 0.4, -r * 0.62), (-r * 0.3, -r * 0.55),
                          (-r * 0.58, -r * 0.2), (-r * 0.64, r * 0.0)], tension=0.45)
            g.shape(cap, col)

    # props held ---------------------------------------------------------------
    def draw_props(self, g, J, p, arms, st):
        if "staff" in self.s["extras"] and not p.get("lie") and not p.get("seat"):
            W = arms["f"][2]
            x = W[0] + 3
            g.line([(x, W[1] - 70), (x + 2, 0)], color="#7a4e2c", w=4.2)
            g.c.drawArc(skia.Rect.MakeLTRB(x - 8, W[1] - 88, x + 8, W[1] - 70), 90, 300, False,
                        g.stroke("#7a4e2c", 4.2))
            g.circle(W[0] + 2, W[1] + 1, self.s["arm_w"] * 0.55, shade(self.s["skin"], 0.12))
        prop = p.get("prop")
        if not prop:
            return
        s = self.s
        if prop == "jar":
            W = arms["n"][2]
            g.shape(smooth([(W[0] - 2, W[1] - 2), (W[0] + 12, W[1] - 4), (W[0] + 15, W[1] + 10), (W[0] + 8, W[1] + 20),
                            (W[0] - 1, W[1] + 12)], tension=0.5), "#a0522d")
            return
        if prop == "money":
            W = arms["n"][2]
            for k in range(3):
                g.shape(rrect(W[0] + 1 + k * 1.2, W[1] - 9 - k * 1.5, 13, 7, 0.8), "#8fa37a")
            return
        if prop == "hoe":
            W = arms["n"][2]
            dx, dy = W[0] - arms["n"][1][0], W[1] - arms["n"][1][1]
            L = math.hypot(dx, dy) or 1
            ux, uy = dx / L, dy / L
            h0 = (W[0] - ux * 30, W[1] - uy * 30)
            h1 = (W[0] + ux * 70, W[1] + uy * 70)
            g.line([h0, h1], color="#8a6a3a", w=3.2)
            g.shape(poly([h1, (h1[0] - uy * 16 + ux * 4, h1[1] + ux * 16 + uy * 4), (h1[0] - uy * 18 - ux * 8, h1[1] + ux * 18 - uy * 8)]),
                    "#6a6660")
            return
        if prop == "broom":
            W = arms["n"][2]; W2 = arms["f"][2]
            g.line([(W2[0] - 4, W2[1] - 14), (W[0] + 22, -2)], color="#8a6a3a", w=2.4)
            g.shape(poly([(W[0] + 14, -1), (W[0] + 34, -1), (W[0] + 30, -12), (W[0] + 20, -12)]), "#c9a867")
            return
        if prop == "paddle":
            W = arms["n"][2]
            g.line([(W[0] - 12, W[1] - 20), (W[0] + 24, W[1] + 50)], color="#7a5a32", w=3)
            return
        if prop == "sack":
            at = J["at_torso"]
            q = at(s["shoulder"] * 0.1, -12)
            g.shape(smooth([(q[0] - 30, q[1] + 4), (q[0] - 20, q[1] - 12), (q[0] + 26, q[1] - 12), (q[0] + 34, q[1] + 4),
                            (q[0] + 20, q[1] + 12), (q[0] - 22, q[1] + 12)], tension=0.4), "#d8cba8")
            g.line([(q[0] - 6, q[1] - 8), (q[0] - 4, q[1] + 8)], color="#b8a882", w=1.2)
            return
        if prop == "cup":
            W = arms["n"][2]
            g.shape(rrect(W[0] + 1, W[1] - 9, 8, 10, 2), "#eef0f0")
            return
        if prop == "money" and self.name in ("owner", "phanit"):
            W = arms["n"][2]
            if self.name == "phanit":
                g.shape(rrect(W[0] + 1, W[1] - 6, 11, 8, 1.5), "#5a3a22")
            else:
                for k in range(3):
                    g.shape(rrect(W[0] + 1 + k * 1.2, W[1] - 9 - k * 1.5, 13, 7, 0.8), "#8fa37a")
        elif prop == "pen":
            W = arms["f"][2]
            g.line([(W[0] + 2, W[1] - 1), (W[0] + 7, W[1] - 9)], color="#1c1c2a", w=1.6)
        elif prop == "ledger_hug":
            at = J["at_torso"]
            q = at(s["shoulder"] * 0.4, 16)
            g.shape(rrect(q[0] - 9, q[1] - 2, 18, 26, 1.5), "#6a2e22")
            g.line([(q[0] - 7, q[1]), (q[0] - 7, q[1] + 22)], color="#e9dfc6", w=1.4)
        elif prop == "book_open":
            at = J["at_torso"]
            q = at(s["shoulder"] * 0.95, 30)
            g.shape(poly([(q[0] - 12, q[1] - 4), (q[0], q[1] - 1), (q[0] + 12, q[1] - 4), (q[0] + 12, q[1] + 6),
                          (q[0], q[1] + 9), (q[0] - 12, q[1] + 6)]), "#efe6cf")
            g.line([(q[0], q[1] - 1), (q[0], q[1] + 9)])


def blend_pose(a, b, t):
    """Interpolate numeric pose params; discrete params switch at t>=0.5."""
    t = ease(t)
    out = {}
    for k in set(a) | set(b):
        va, vb = a.get(k, STAND.get(k)), b.get(k, STAND.get(k))
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)) and not isinstance(va, bool):
            out[k] = va + (vb - va) * t
        else:
            out[k] = vb if t >= 0.5 else va
    return out


# ───────────────────────────────────────────────────────────── story extension
# A story folder may add its own locked characters / poses in story_chars.py (it does `import chars` and
# updates chars.CAST / chars.POSES / chars.BASE_POSES). Loaded here so every engine script sees them.
def _load_story_chars():
    import os, sys, importlib
    sd = os.environ.get("STORY_DIR")
    if sd and os.path.exists(os.path.join(sd, "story_chars.py")):
        if sd not in sys.path:
            sys.path.insert(0, sd)
        importlib.import_module("story_chars")
_load_story_chars()
