# Story folder format

A story folder has two files: `script_data.py` (the screenplay) and `project.py` (everything else the engine needs).
Start from `templates/story/`; the full example is `examples/preah-atit/story/`.

## script_data.py
```python
CHARACTERS = {"narrator": dict(kh="អ្នកនិទាន", en="Narrator"), "sam": dict(kh="សម", en="Sam"), ...}
SCENES = [
  dict(n=1, ch=1, title_kh="ពីជនបទ", title_en="From the Countryside", source="summary ¶1",
       music="opening", amb="country", loc="village", tod="dawn",
       cast=["sam", "soy"],
       start=dict(sam=(-60, 0.15, "hoe", 1), soy=(700, 0.1, "stand", -1)),   # x, depth, base pose, facing
       items=[
         X("establish", 8.0, "Sunrise over the fields.", cam="insert:village_sunrise", sfx=["birds_morning"]),
         L("soy", "បងសម សម្រាកផឹកទឹកសិនទៅ។", "Sam, rest and drink some water.", "gentle", "holds out the jar",
           cam="med:soy", pose={"soy": "offer"}),
         L("narrator", "ចុងទសវត្សរ៍ ១៩៥០។", "The late 1950s.", "calm", "", cam="wide",
           tts="ចុងទសវត្សរ៍ឆ្នាំមួយពាន់ប្រាំបួនរយហាសិប។"),     # numbers spelled out for TTS
       ]),
]
VOICE_OF = {"sam_prison": "sam"}          # costume variants speak with the base character's voice
```
- `L(speaker, khmer, english, emotion, action, cam=, pose=, move=, sfx=, tts=, pause=)` — a dialogue line. The
  emotion words drive the facial expression (`chars.expr_for`: e.g. "worried", "angry", "cry", "calm", "firm").
  `action` containing `inner voice` disables lip movement; `push-in` gives a slow push-in.
- `X(kind, seconds, description, cam=, sfx=, pose=, move=)` — a shot without dialogue.
  kinds: `establish`, `action`, `insert`, `reaction`, `ending`.
- **Cameras**: `wide` · `two:A,B` · `med:A` · `mcu:A` · `cu:A` · `ots:A>B` (over A's shoulder onto B) ·
  `insert:<name>` (a cut-away drawn in `render.draw_insert`).
- **Moves**: `to:X,D` · `near:NAME` · `exit_left` · `exit_right` (a speaker leaves after the line ends).
- **Poses** (`pose={id: name}`): base poses persist (`stand sit sit_sad sit_work sit_pray desk write look_up kneel
  kneel_sampeah kneel_grief work hoe sweep stir carry hold_cup cyclo bed lie hand_belly head_down`); others are
  gestures for the length of the line (`point offer offer_money sampeah hand_chest stop_hand arms_up arms_crossed
  hands_face fists shock gesture_sit hush`).
- **Locations** (`loc`): `village street yard hut temple villa meyhome prison visit newhome factory hall office clinic
  mansion ward`. **Time of day** (`tod`): `dawn day evening dusk dusk_rain night`.
- **Music cues**: `opening city hardship threat temple confront prison hope workers neutral tragedy lowest reflect
  sunrise` (+ the originals in `audio_synth.py`). **Ambience** (`amb`): `country street temple house house_poor night
  rain_in rain_out prison factory crowd_room clinic hospital train river market office`.
- **SFX**: any name in `audio_extra.py` (`_raw`) or `audio_synth.SFX_NAMES`.

## project.py
```python
TITLE_KH, TITLE_EN, SOURCE, OUT_MP4, CREDIT_KH
CHAPTERS = {1: ("ពីជនបទ", "From the Countryside"), ...}
VOICES = {"sam": "A Cambodian young man about twenty-five, warm clear medium male voice, ..."}   # VoxCPM2 voice design
REF_TEXT = {"sam": "ខ្ញុំឈ្មោះសម។ ..."}                     # a natural Khmer sentence the voice reads when designed
CHOICE = {"sam": "s202", "soy": None}                      # lock a candidate seed, or None = automatic
REUSE_LOCK = None; REUSE = {}; NARRATOR_FROM_REUSE = None   # reuse installed voices from another project
PROFILE = {"sam": ("male", "25", 0.98, "hopeful / tired / angry")}
INFO = {"sam": ("role", "age", "body", "default expression", "costume notes")}   # character bible
MUTES = [(19, "kind:reaction|speaker:sam")]                # music drops out for the hardest moments
CONTINUITY_NOTES = ["[OK] ... story-specific notes for the continuity report"]
```
If there is no reuse file, list a `narrator` in `VOICES`/`REF_TEXT`/`PROFILE` so it is designed like the others.

## Characters
Rig specs live in `engine/chars.py → CAST` (height, head size, skin, hair style, shirt style/colours, pants/skirt,
extras such as `krama_neck`, `glasses`, `cap_police`, `stethoscope` …). Add new characters there; draw a sheet with
`sheet.py <id>` and review it before rendering scenes.
