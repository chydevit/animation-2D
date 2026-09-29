# -*- coding: utf-8 -*-
"""Project settings for this story (everything film-specific that the engine needs besides script_data.py)."""

# ── titles and credits
TITLE_KH = "ព្រះអាទិត្យថ្មីរះលើផែនដីចាស់"
TITLE_EN = "A New Sun Rises Over the Old Land"
SOURCE = ("https://www.khsearch.com/qna/19257 — summary of the novel by សួន សុរិន្ទ (composed 1960-61); "
          "dialogue is an original cinematic adaptation, not a quotation of the novel")
OUT_MP4 = "preah_atit_thmey_reah_leu_phendey_chas.mp4"
CREDIT_KH = "ផ្អែកលើប្រលោមលោករបស់ លោក សួន សុរិន្ទ"      # small line under the title card

# ── chapter cards (chapter number -> (Khmer title, English title))
CHAPTERS = {
    1: ("ពីជនបទ", "From the Countryside"), 2: ("ជីវិតអ្នកធាក់ស៊ីក្លូ", "Cyclo Life in Phnom Penh"),
    3: ("បាត់ផ្ទះ បាត់ការងារ", "Losing Home and Work"), 4: ("ការល្បួង", "The Temptation"),
    5: ("សយទៅធ្វើការ", "Soy Goes to Work"), 6: ("កំហឹងរបស់សម", "Sam's Anger"), 7: ("គុក", "Prison"),
    8: ("ឱកាសថ្មី", "A New Chance"), 9: ("ជម្លោះកន្លែងការងារ", "Workplace Conflict"),
    10: ("កម្មករ និងការខកចិត្ត", "Workers and Disappointment"), 11: ("សោកនាដកម្មក្នុងគ្រួសារ", "Family Tragedy"),
    12: ("ចំណុចទាបបំផុត និងព្រះអាទិត្យថ្មី", "The Lowest Point and a New Sun"),
}

# ── voices: VoxCPM2 voice-design prompt + reference sentence per speaking character
VOICES = {
  "sam":      "A Cambodian young man about twenty-five, warm clear medium male voice, sincere, a little tired",
  "soy":      "A Cambodian young woman about twenty-two, soft gentle sweet female voice, calm and kind",
  "mey":      "A Cambodian man about thirty-five, deep low steady warm male voice, calm and practical",
  "mom":      "A Cambodian woman about thirty, warm caring bright female voice, speaks kindly",
  "kimleang": "A Cambodian woman about forty-five, firm sharp businesslike female voice, a little cold",
  "tasan":    "An old Cambodian man about sixty-five, thin raspy elderly male voice, grumpy",
  "sau":      "A Cambodian man about thirty, rough low street-smart male voice, speaks slowly and slyly",
  "broker":   "An old Cambodian woman about sixty, chatty quick friendly elderly female voice",
  "hok":      "A Cambodian businessman about fifty, deep smooth male voice, cold, calm and controlled, speaks clearly",
  "police":   "A Cambodian policeman about thirty-five, firm strict clear deep male voice, speaks steadily",
  "chhuoy":   "An old Cambodian man about seventy, slow deep gentle wise male voice, calm",
  "yaykan":   "An elderly Cambodian woman about seventy, soft slow kind grandmotherly voice",
  "worker":   "A young Cambodian man about twenty-eight, cheerful friendly clear male voice",
  "sengly":   "A Cambodian-Chinese factory owner about sixty, calm deep measured male voice, polite",
  "sengan":   "A Cambodian-Chinese man about thirty-five, polite soft mild male voice",
  "senghong": "A young Cambodian-Chinese man about twenty-eight, sharp arrogant nasal male voice, impatient",
  "yeng":     "A Cambodian man about forty-five, deep smooth confident male voice, persuasive and polished",
  "nara":     "A Cambodian doctor about fifty, serious calm low male voice, careful and tired",
  "oknha":    "A rich old Cambodian nobleman about sixty-five, heavy deep proud male voice, harsh",
  "minister": "A young Cambodian government minister about thirty-five, clear educated kind male voice",
}
REF_TEXT = {
  "sam":      "ខ្ញុំឈ្មោះសម។ ខ្ញុំមកពីស្រុកស្រែ ហើយខ្ញុំចង់រកការងារសុចរិត ដើម្បីចិញ្ចឹមប្រពន្ធខ្ញុំ។",
  "soy":      "ខ្ញុំឈ្មោះសយ។ ខ្ញុំចេះបោកខោអាវ ចម្អិនម្ហូប ហើយខ្ញុំតែងតែនៅក្បែរប្ដីខ្ញុំជានិច្ច។",
  "mey":      "ខ្ញុំធាក់ត្រីចក្រយានរាល់ថ្ងៃ។ ការងារនេះហត់មែន តែបើយើងជួយគ្នា អ្វីៗនឹងស្រួលជាងមុន។",
  "mom":      "ចូលមកផ្ទះសិនទៅ។ ខ្ញុំទើបតែដាំបាយឆ្អិន។ អង្គុយហូបជាមួយគ្នាសិនមក។",
  "kimleang": "ស៊ីក្លូរបស់ខ្ញុំ មិនមែនឲ្យគេជួលទទេៗទេ។ រាល់ល្ងាច ត្រូវយកលុយមកបង់ឲ្យគ្រប់។",
  "tasan":    "ខ្ទមនេះជារបស់ខ្ញុំ។ អ្នកណាចង់នៅ ត្រូវតែបង់ថ្លៃជួលរាល់ខែ កុំឲ្យខ្វះ។",
  "sau":      "នៅទីក្រុងនេះ អ្នកណាឆ្លាត អ្នកនោះបានស៊ី។ អ្នកល្ងង់ ត្រូវតែអត់ឃ្លានរហូត។",
  "broker":   "ក្មួយអើយ យាយស្គាល់ផ្ទះអ្នកមានច្រើនណាស់។ បើក្មួយខំធ្វើការ គេនឹងឲ្យលុយច្រើន។",
  "hok":      "ផ្ទះនេះជាផ្ទះរបស់ខ្ញុំ។ អ្នកណាធ្វើការនៅទីនេះ ត្រូវតែស្ដាប់បង្គាប់ខ្ញុំ។",
  "police":   "ឈប់សិន! បង្ហាញក្រដាសរបស់អ្នកមក។ នៅទីនេះ អ្នកណាក៏ត្រូវគោរពច្បាប់ដែរ។",
  "chhuoy":   "ក្មួយអើយ ជីវិតមនុស្ស ដូចទឹកទន្លេ។ មានពេលឡើង ហើយក៏មានពេលស្រកដែរ។",
  "yaykan":   "យាយចាស់ហើយ ក្មួយ។ យាយគ្រាន់តែចង់ឃើញក្មេងៗ រស់នៅដោយសុខសប្បាយ។",
  "worker":   "ថ្ងៃនេះ យើងត្រូវលើកបាវបីរយ។ ទៅ! ជួយគ្នាលើក ឆាប់ហើយឆាប់សម្រាក។",
  "sengly":   "រោងចក្រសាប៊ូនេះ ខ្ញុំបើកតាំងពីដប់ឆ្នាំមុន។ ខ្ញុំចូលចិត្តកម្មករដែលស្មោះត្រង់។",
  "sengan":   "សូមអញ្ជើញតាមខ្ញុំមក។ ខ្ញុំនឹងបង្ហាញពីរបៀបធ្វើការនៅក្នុងរោងចក្រនេះ។",
  "senghong": "ខ្ញុំមិនចង់ឮពាក្យដោះសារទេ។ ធ្វើការឲ្យលឿនជាងនេះ បើមិនចង់ចេញ។",
  "yeng":     "បងប្អូនទាំងអស់គ្នា! ខ្ញុំនឹងធ្វើការដើម្បីបងប្អូន។ សូមជឿលើខ្ញុំ!",
  "nara":     "អ្នកជំងឺត្រូវការសម្រាក។ ខ្ញុំនឹងពិនិត្យម្ដងទៀត ហើយឲ្យថ្នាំតាមពេលវេលា។",
  "oknha":    "ទ្រព្យសម្បត្តិទាំងនេះ ជារបស់ត្រកូលខ្ញុំ។ គ្មាននរណាហ៊ានប៉ះពាល់ឡើយ។",
  "minister": "ខ្ញុំចង់ជួយប្រជាជនដែលពិបាក។ ការងារល្អ ចាប់ផ្ដើមពីចិត្តស្មោះត្រង់។",
}

# ── which designed candidate to lock (seed tag), or None = pick automatically by pitch/stability
CHOICE = {
    "sam": "s202", "soy": "s202", "mey": None, "mom": "s202", "kimleang": "s202", "tasan": "s202",
    "sau": "s202", "broker": "s202", "hok": None, "police": None, "chhuoy": "s101", "yaykan": "s202",
    "worker": None, "sengly": "s101", "sengan": "s101", "senghong": "s202", "yeng": None, "nara": "s202",
    "oknha": "s101", "minister": "s202",
}
# ── roles that reuse an already-installed voice from another project: role -> (voice_lock.json path, voice id)
REUSE_LOCK = "../thavke_chett_chaor/audio/voices/voice_lock.json"   # relative to the episode folder; missing file = design all voices
REUSE = {"mey": "kong", "hok": "owner", "police": "agent", "worker": "trey", "yeng": "chief"}
NARRATOR_FROM_REUSE = "narrator"   # reuse the narrator voice from REUSE_LOCK (None = design one)
PROFILE = {   # gender, age impression, speaking-rate, emotional range (locked with the voice)
    "narrator": ("female", "40s", 0.94, "warm-serious"),
    "sam": ("male", "25", 0.98, "hopeful / tired / angry / grieving / determined"),
    "soy": ("female", "22", 0.96, "gentle / worried / hopeful / distressed"),
    "mey": ("male", "35", 1.0, "steady / protective / wise"), "mom": ("female", "30", 1.0, "warm / worried"),
    "kimleang": ("female", "45", 1.0, "firm / cold"), "tasan": ("male", "65", 0.95, "grumpy / tired"),
    "sau": ("male", "30", 0.95, "sly / cynical / cold"), "broker": ("female", "60", 1.05, "chatty / kind"),
    "hok": ("male", "50", 0.97, "controlled / cold / false alarm"), "police": ("male", "35", 1.0, "stern / official"),
    "chhuoy": ("male", "70", 0.9, "wise / calm"), "yaykan": ("female", "70", 0.9, "kind / gentle"),
    "worker": ("male", "28", 1.05, "friendly / weary"), "sengly": ("male", "60", 0.95, "calm / official"),
    "sengan": ("male", "35", 1.0, "polite / kind"), "senghong": ("male", "28", 1.05, "cold / harsh"),
    "yeng": ("male", "45", 1.0, "eager / dismissive"), "nara": ("male", "50", 0.95, "serious / grave"),
    "oknha": ("male", "65", 0.95, "harsh"), "minister": ("male", "35", 1.0, "kind / thoughtful / warm"),
}

# ── character bible notes: id -> (role, age, body type, default expression, costume notes)
INFO = {   # role, age, body type, default expression, costume notes (story-driven changes only)
  "sam": ("Main protagonist; young orphaned farmer", "about 25", "slim, average height", "tired but determined",
          "faded blue-grey short-sleeve shirt, brown rolled trousers, red-white checked krama at the neck, sandals"),
  "sam_prison": ("Costume variant of SAM (prison, ch. 7)", "about 25", "same as SAM", "sad",
                 "grey prison shirt and trousers; stubble. Face, hair, skin and body = SAM"),
  "sam_ragged": ("Costume variant of SAM (homeless, ch. 12)", "about 26", "same as SAM, visibly exhausted", "tired",
                 "same shirt colour family, worn and patched, open collar; untidy hair, stubble, tired eyes. Face = SAM"),
  "soy": ("Sam's wife; orphan, gentle and loyal", "about 22", "small, slim", "gentle",
          "dusty-rose blouse, dark purple woven sarong, green-white krama over one shoulder, hair in a low bun"),
  "soy_preg": ("Costume variant of SOY (pregnant, ch. 11)", "about 23", "same as SOY with pregnant belly", "tender",
               "same outfit; pregnant. Face, hair, skin = SOY"),
  "mey": ("Sam's friend, pedicab (tricycle) worker; practical adviser", "about 35", "broad, strong", "calm",
          "dark-blue work shirt with rolled sleeves, black rolled trousers, blue-white krama at the neck"),
  "mom": ("Mey's household; Soy's warm friend", "about 30", "medium", "kind",
          "mustard-yellow blouse, rust-red sarong, long hair tied at the back"),
  "kimleang": ("Cyclo owner who rents to Sam", "about 45", "sturdy", "firm",
               "white long-sleeve blouse, navy sarong with gold border, high chignon, gold earrings, wristwatch"),
  "tasan": ("Elderly landlord of the hut", "about 65", "thin, slightly stooped", "stern",
            "grey singlet, dark rolled trousers, red krama at the neck, grey untidy hair, stubble"),
  "sau": ("Leader of a snatch-theft gang; a struggling man of the same streets", "about 30", "lean, tall", "sly",
          "black open-collar shirt with red undershirt, dark green trousers, spiky hair, stubble, small cheek scar"),
  "broker": ("Old woman who finds Soy the housemaid job", "about 60", "small, round", "chatty",
             "purple long-sleeve blouse, dark sarong, grey bun"),
  "hok": ("Wealthy employer (Boss Hok)", "about 50", "heavy, big belly", "controlled",
          "maroon short-sleeve shirt, black trousers, leather shoes, slicked hair, thin moustache, gold watch"),
  "police": ("Policeman (traffic post, arrests)", "about 35", "solid", "stern",
             "khaki uniform with cap and badge, black belt, whistle, moustache"),
  "police2": ("Second policeman", "about 28", "average", "serious", "khaki uniform with cap, black belt"),
  "chhuoy": ("Old prisoner who counsels Sam (Phu Chhuoy)", "about 70", "thin", "wise",
             "grey prison clothes, short white hair, white beard"),
  "huor": ("Older inmate (seen only as shadow/background)", "about 40", "big, heavy", "angry", "grey prison clothes"),
  "suos": ("Older inmate (seen only as shadow/background)", "about 32", "wiry", "angry", "grey prison clothes"),
  "guard": ("Office guard", "about 35", "solid", "serious", "olive uniform and cap"),
  "yaykan": ("Kind wealthy widow who gives Sam a cyclo (Grandma Kan)", "about 70", "small", "kind",
             "white long-sleeve blouse, green sarong with gold border, purple-white krama, gold necklace, white bun"),
  "worker": ("Soap-factory worker, Sam's co-worker", "about 28", "medium", "friendly",
             "orange work shirt with rolled sleeves, white headband, wavy hair"),
  "worker2": ("Worker", "about 40", "stocky", "neutral", "green singlet, brown rolled trousers, moustache"),
  "worker3": ("Worker / cyclo rider in the street", "about 22", "slim", "neutral", "cream shirt, blue rolled trousers"),
  "sengly": ("Soap-factory owner (Boss Seng Ly)", "about 60", "portly", "calm",
             "white mandarin-collar shirt with gold buttons, dark trousers, grey slicked hair, round glasses"),
  "sengan": ("Seng Ly's assistant, later sent to Hong Kong", "about 35", "slim", "polite",
             "white short-sleeve shirt with pocket pen, taupe trousers"),
  "senghong": ("Seng Ly's nephew, manager in his absence", "about 28", "tall", "cold",
               "tan jacket over white shirt, light trousers, pompadour hair, gold watch"),
  "yeng": ("Election candidate, later elected (Mr. Yeng)", "about 45", "heavy-set", "eager",
           "cream suit, dark red tie, round glasses, moustache"),
  "nara": ("Doctor across the river (Doctor Nara)", "about 50", "average", "serious",
           "white doctor's coat, stethoscope, round glasses, greying hair"),
  "oknha": ("Wealthy nobleman whose goods Sam returns", "about 65", "very heavy", "harsh",
            "white high-collar jacket with medal, purple rolled sampot, balding grey hair, moustache"),
  "minister": ("Young minister whose car hits Sam", "about 35", "tall, slim", "kind",
               "light-grey suit, navy tie, neat side-parted hair"),
}

# ── music drop-outs for the most painful moments: (scene number, rule) — music fades out from the first
#    matching shot to the end of the scene (rules: "kind:<kind>", "speaker:<id>", "cam:<camera>", joined by |)
MUTES = [(19, "kind:reaction|speaker:sam"), (7, "cam:insert:closed_door|cam:insert:black")]

# ── story-specific lines for docs/continuity_report.txt (costume logic, sensitive-content handling)
CONTINUITY_NOTES = [
    '[OK] costume changes only where the story requires: SAM_PRISON (prison, scenes 10-12), SAM_RAGGED (homeless/theft,',
    '     scenes 20-22), SOY_PREG (pregnancy, scene 18). Variants share face, hair, skin and body with the base character.',
    "[OK] sensitive events are implied only: Soy's assault = footsteps, dropped cup, closed door, rain, fade to black,",
    "     next-morning aftermath (scene 7); prison mistreatment = shadows on a wall (scene 10); Soy's death = closed",
    "     door, doctor's lowered head, 5 s of silence, no music (scene 19); theft = aftermath only, no technique (scene 20)",
    '[OK] political material neutral: one fictional candidate (Mr. Yeng), no party names, slogans, or modern references;',
    "     Sam's conclusion is personal ('I won't be used as a stepping-stone again'). The source's closing praise of",
    '     specific leaders is not included; the ending keeps only the event (peace; Sam returns to farming).',
]
