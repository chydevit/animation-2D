# -*- coding: utf-8 -*-
"""Starter screenplay: two short scenes with Sam and Soy (characters from engine/chars.py) and a narrator.
Replace with your own story (see references/screenplay-format.md)."""

def L(sp, kh, en, emo="", act="", cam=None, pose=None, move=None, sfx=None, tts=None, pause=0.25):
    return dict(type="line", sp=sp, kh=kh, en=en, emo=emo, act=act, cam=cam,
                pose=pose or {}, pause=pause, tts=tts or kh, move=move or {}, sfx=sfx or [])

def X(kind, dur, desc, cam="wide", sfx=None, pose=None, move=None):
    return dict(type="shot", kind=kind, dur=dur, desc=desc, cam=cam, sfx=sfx or [], pose=pose or {}, move=move or {})

CHARACTERS = {
    "narrator": dict(kh="អ្នកនិទាន", en="Narrator"),
    "sam": dict(kh="សម", en="Sam"),
    "soy": dict(kh="សយ", en="Soy"),
}

SCENES = [
dict(n=1, ch=1, title_kh="ព្រឹកព្រលឹម", title_en="Early Morning", source="template", music="opening", amb="country",
     loc="village", tod="dawn", cast=["sam", "soy"],
     start=dict(sam=(-60, 0.15, "hoe", 1), soy=(700, 0.1, "stand", -1)),
     items=[
  X("establish", 6.0, "Sunrise over the rice fields.", cam="insert:village_sunrise", sfx=["birds_morning"]),
  L("narrator", "នៅភូមិតូចមួយ មានប្ដីប្រពន្ធពីរនាក់ ខំធ្វើស្រែជារៀងរាល់ថ្ងៃ។",
    "In a small village, a husband and wife worked the fields every day.", "calm", "", cam="wide"),
  X("action", 3.5, "Soy walks along the dyke with a water jar.", cam="wide", move={"soy": "to:120,0.12"}),
  L("soy", "បង សម្រាកផឹកទឹកសិនទៅ។", "Rest and drink some water.", "gentle", "", cam="med:soy", pose={"soy": "offer"}),
  L("sam", "អរគុណអូន។ ថ្ងៃនេះ ស្រែយើងស្អាតណាស់។", "Thank you. Our field looks beautiful today.", "happy", "",
    cam="med:sam", pose={"sam": "stand"}, pause=0.6),
]),
dict(n=2, ch=1, title_kh="ពេលល្ងាច", title_en="Evening", source="template", music="sunrise", amb="night",
     loc="hut", tod="night", cast=["sam", "soy"],
     start=dict(sam=(-120, 0.1, "sit", 1), soy=(60, 0.12, "sit", -1)),
     items=[
  L("soy", "ស្អែក យើងទៅផ្សារជាមួយគ្នាណា។", "Tomorrow let's go to the market together.", "hopeful", "", cam="two:sam,soy"),
  L("sam", "បាន។ ឥឡូវ សម្រាកសិនចុះ។", "Yes. Now, let's rest.", "calm", "", cam="mcu:sam", pause=0.8),
  X("ending", 6.0, "Title card.", cam="insert:title_end"),
]),
]

VOICE_OF = {}
def voice_of(sp):
    return VOICE_OF.get(sp, sp)

def all_lines():
    return [(s["n"], it) for s in SCENES for it in s["items"] if it["type"] == "line"]
