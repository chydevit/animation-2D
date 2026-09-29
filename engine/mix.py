# Audio mix, subtitles, scenes.json, screenplay text and final MP4 assembly.
#   ~/anim-env/bin/python mix.py audio      -> audio/mix.wav (+ stems)
#   ~/anim-env/bin/python mix.py docs       -> subtitles_kh.srt, subtitles_en.srt, scenes.json, screenplay_khmer.txt
#   ~/anim-env/bin/python mix.py assemble   -> <episode>/preah_atit_thmey_reah_leu_phendey_chas.mp4
import os, sys, json, math, subprocess, textwrap
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
import audio_extra as AS
import config
from plan import build, FINAL, DOCS, FPS, LEAD
from script_data import SCENES, CHARACTERS, voice_of

SR = 48000
DLG = os.path.join(FINAL, "audio", "dialogue")
ADIR = os.path.join(FINAL, "audio")
VOICE_LOCK = os.path.join(ADIR, "voices", "voice_lock.json")

def db(x):
    return 10 ** (x / 20)

def place(buf, x, t, gain=1.0):
    i0 = int(round(t * SR))
    if i0 >= len(buf):
        return
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    n = min(len(x), len(buf) - i0)
    if i0 < 0:
        x = x[-i0:]; n = min(len(x), len(buf)); i0 = 0
    buf[i0:i0 + n] += x[:n] * gain

def smooth_env(x, att=0.05, rel=0.35):
    a1, a2 = math.exp(-1 / (att * SR / 256)), math.exp(-1 / (rel * SR / 256))
    blocks = np.sqrt(np.mean(x[: len(x) // 256 * 256].reshape(-1, 256) ** 2, axis=1))
    out = np.zeros_like(blocks); v = 0
    for i, b in enumerate(blocks):
        v = a1 * v + (1 - a1) * b if b > v else a2 * v + (1 - a2) * b
        out[i] = v
    r = np.repeat(out, 256)
    return np.pad(r, (0, max(0, len(x) - len(r))), mode="edge")[: len(x)]

def music_segments(tl):
    """one cue per scene; returns (t0, t1, cue) plus mute windows (silence for the most painful moments)."""
    segs, mutes = [], []
    rules = {n: r.split("|") for n, r in getattr(config.P, "MUTES", [])}
    def hit(sh, rule):
        k, _, v = rule.partition(":")
        return (k == "kind" and sh.get("kind") == v) or (k == "speaker" and sh.get("speaker") == v) or \
               (k == "cam" and (sh.get("cam") or "") == v)
    for sc in tl["scenes"]:
        segs.append((sc["t0"], sc["t1"], sc["music"]))
        if sc["n"] in rules:
            r = [s for s in sc["shots"] if any(hit(s, rr) for rr in rules[sc["n"]])]
            if r:
                last = r[-1]["t1"] if all(rr.startswith("cam:") for rr in rules[sc["n"]]) else sc["t1"]
                mutes.append((r[0]["t0"] - 0.4, last))
    return segs, mutes

AMB_FOR_INSERT = {"village_sunrise": "country", "train": "train", "city_street": "street", "fine_slip": "street",
                  "temple_ext": "temple", "villa_ext": "street", "villa_rain": "rain_out", "cup_drop": "rain_in",
                  "closed_door": "rain_in", "black": "rain_in", "morning_gate": "street", "night_gate": "night",
                  "court": "office", "prison_ext": "street", "prison_shadow": "prison", "prison_release": "street",
                  "pedicab_ride": "street", "cyclo_ride": "street", "car_hit": "street", "car_hit2": "street",
                  "hospital_bed": "hospital", "factory_ext": "country", "factory_room": "house_poor",
                  "job_montage": "factory", "campaign": "market", "river_night": "river", "funeral": "temple",
                  "homeless_night": "rain_out", "market": "market", "alley": "night", "prison_window": "prison",
                  "garden": "country", "final_sunrise": "country", "title_end": None}
SFX_GAIN = {"car_arrive": -8, "car_depart": -9, "traffic_old": -12, "police_whistle": -12, "heartbeat_soft": -9,
            "crowd_murmur": -12, "pen_write": -8, "paper_page": -8, "footsteps_sandal": -7, "footsteps_concrete": -6,
            "footsteps_wood": -6, "footsteps_dirt": -8, "birds_morning": -12, "birds_city": -16, "rain_heavy": -8,
            "thunder_far": -6, "temple_bell": -10, "metal_door": -6, "cup_break": -8, "car_brake": -6, "thud": -4,
            "train_run": -8, "cyclo_bell": -12, "cyclo_chain": -14, "crickets": -14, "room_tone": -14, "scuffle": -10,
            "clock_tick": -12, "factory_hum": -12, "market_amb": -12, "dog_far": -16, "drip": -12, "gate_shut": -8}

def build_audio():
    tl = build()
    total = tl["total"]
    N = int(total * SR) + SR
    dlg = np.zeros((N, 2), np.float32)
    mus = np.zeros((N, 2), np.float32)
    amb = np.zeros((N, 2), np.float32)
    fx = np.zeros((N, 2), np.float32)
    # dialogue
    ROOM = {"hut": (0.45, 0.07), "meyhome": (0.5, 0.07), "newhome": (0.3, 0.03), "villa": (0.9, 0.09),
            "mansion": (1.1, 0.10), "prison": (1.4, 0.13), "visit": (1.0, 0.10), "factory": (1.3, 0.11),
            "hall": (0.8, 0.08), "clinic": (0.8, 0.08), "ward": (0.9, 0.09), "yard": (0.5, 0.05)}
    INS_OUT = ("village_sunrise", "train", "city_street", "temple_ext", "villa_ext", "morning_gate", "night_gate",
               "prison_ext", "prison_release", "pedicab_ride", "cyclo_ride", "campaign", "river_night", "market",
               "alley", "garden", "final_sunrise", "homeless_night", "car_hit", "car_hit2")
    for sh in tl["shots"]:
        if sh.get("audio"):
            y, sr = sf.read(os.path.join(DLG, sh["audio"]), dtype="float32")
            if y.ndim > 1: y = y.mean(1)
            if sr != SR: y = resample_poly(y, SR, sr).astype(np.float32)
            # loudness-match every line: RMS of the voiced part -> -20 dBFS, then a clarity lift + rumble cut
            fr = np.abs(y[: len(y) // 480 * 480]).reshape(-1, 480).mean(1)
            act = fr > max(1e-4, 0.15 * fr.max())
            rms = np.sqrt(np.mean(y[: len(act) * 480].reshape(-1, 480)[act] ** 2)) if act.any() else 0.05
            y = y * (db(-20) / max(rms, 1e-4))
            y = AS.hp(y, 80)
            y = AS.AS.peaking(y, 3200, 2.0, 0.8) if hasattr(AS, "AS") else y
            y = np.clip(y, -0.97, 0.97).astype(np.float32)
            st = np.stack([y, y], 1)
            cam = sh.get("cam") or ""
            ins = cam.split(":", 1)[1] if cam.startswith("insert:") else None
            room = None if (sh["speaker"] == "narrator" or (ins in INS_OUT) or
                            (ins is None and sh["loc"] in ("village", "street", "temple", "office"))) else \
                   ROOM.get(sh["loc"] if ins is None else "ward" if ins == "hospital_bed" else sh["loc"])
            if room:
                st = AS.reverb(st, rt=room[0], wet=room[1], damp=5000, predelay=0.012, tail=True, seed=3)
            g = db(-1.5) if sh["speaker"] != "narrator" else db(-2.5)
            place(dlg, st, sh["speech"][0], g)
    # music with crossfades
    segs, mutes = music_segments(tl)
    for (t0, t1, cue) in segs:
        dur = t1 - t0 + 2.0
        m = AS.music(cue, dur, seed=int(t0) % 97)
        fade = int(1.0 * SR)
        m[:fade] *= np.linspace(0, 1, fade)[:, None]
        place(mus, m, max(0, t0 - 1.0))
    for (m0, m1) in mutes:
        i0, i1 = int(m0 * SR), int(m1 * SR)
        r = int(1.5 * SR)
        mus[i0:i0 + r] *= np.linspace(1, 0, min(r, len(mus[i0:i0 + r])))[:, None]
        mus[i0 + r:i1] = 0
    # ambience: per scene (garage), with insert overrides
    for sc in tl["scenes"]:
        for sh in sc["shots"]:
            cam = sh.get("cam") or ""
            kind = AMB_FOR_INSERT.get(cam.split(":", 1)[1], sc["amb"]) if cam.startswith("insert:") else sc["amb"]
            if not kind:
                continue
            a = AS.ambience(kind, sh["dur"] + 0.6, seed=sh["idx"] + sc["n"] * 100)
            f = int(0.3 * SR)
            a[:f] *= np.linspace(0, 1, f)[:, None]; a[-f:] *= np.linspace(1, 0, f)[:, None]
            place(amb, a, sh["t0"] - 0.3)
    # sfx
    for sh in tl["shots"]:
        off = 0.1
        for name in sh.get("sfx", []):
            try:
                x = AS.sfx(name, seed=sh["idx"])
            except Exception as e:
                print("sfx fail", name, e); continue
            place(fx, x, sh["t0"] + off, db(SFX_GAIN.get(name, -8) + 4))
            off += 0.7
    # ducking: music & ambience dip under dialogue
    env = smooth_env(dlg.mean(1))
    duck = 1.0 - 0.72 * np.clip(env / 0.05, 0, 1)
    mus *= (db(-14) * duck)[:, None]
    amb *= (db(-19) * (1 - 0.35 * np.clip(env / 0.05, 0, 1)))[:, None]
    mixb = dlg + mus + amb + fx
    # soft limiter
    pk = np.abs(mixb).max()
    mixb = np.tanh(mixb * 1.1) / np.tanh(1.1) if pk > 0.95 else mixb
    for name, arr in (("stem_dialogue", dlg), ("stem_music", mus), ("stem_ambience", amb), ("stem_sfx", fx), ("mix", mixb)):
        sf.write(os.path.join(ADIR, name + ".wav"), arr, SR, subtype="PCM_16")
    # library copies: one file per music cue and per SFX used (for re-use / recovery)
    md = os.path.join(ADIR, "music"); xd = os.path.join(ADIR, "sfx")
    os.makedirs(md, exist_ok=True); os.makedirs(xd, exist_ok=True)
    for cue in sorted({c for _, _, c in segs}):
        sf.write(os.path.join(md, f"{cue}.wav"), AS.music(cue, 45.0, seed=1), SR, subtype="PCM_16")
    for name in sorted({n for sh in tl["shots"] for n in sh.get("sfx", [])}):
        sf.write(os.path.join(xd, f"{name}.wav"), AS.sfx(name, seed=1), SR, subtype="PCM_16")
    print(f"audio: {total/60:.2f} min, peak {np.abs(mixb).max():.2f}")

# ───────────────────────────────────────────────────────────── subtitles & docs
def ts(t):
    t = max(0, t)
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)) % 1000:03d}"

def wrap_kh(s, width=46):
    if len(s) <= width:
        return s
    words = s.split(" ")
    best, bi = None, None
    acc = 0
    for i, w in enumerate(words[:-1]):
        acc += len(w) + 1
        d = abs(acc - len(s) / 2)
        if best is None or d < best:
            best, bi = d, i
    return " ".join(words[:bi + 1]) + "\n" + " ".join(words[bi + 1:])

def subtitles():
    tl = build()
    lines = [s for s in tl["shots"] if s.get("speech")]
    out_kh, out_en = [], []
    for k, sh in enumerate(lines):
        s0, s1 = sh["speech"]
        nxt = lines[k + 1]["speech"][0] if k + 1 < len(lines) else s1 + 2
        e = min(s1 + 0.35, nxt - 0.05)
        if e - s0 < 1.0:
            e = min(s0 + 1.0, nxt - 0.05)
        name_kh = CHARACTERS[sh["speaker"]]["kh"]
        name_en = CHARACTERS[sh["speaker"]]["en"]
        out_kh.append(f"{k+1}\n{ts(s0)} --> {ts(e)}\n{wrap_kh(sh['kh'])}\n")
        en = "\n".join(textwrap.wrap(sh["en"], 44)[:3])
        out_en.append(f"{k+1}\n{ts(s0)} --> {ts(e)}\n{en}\n")
    open(os.path.join(FINAL, "subtitles_kh.srt"), "w", encoding="utf-8").write("\n".join(out_kh))
    open(os.path.join(FINAL, "subtitles_en.srt"), "w", encoding="utf-8").write("\n".join(out_en))
    print("subtitles:", len(lines))

TITLE_KH, TITLE_EN, SOURCE, OUT_MP4 = config.P.TITLE_KH, config.P.TITLE_EN, config.P.SOURCE, config.P.OUT_MP4

def shot_id(sc, sh, tl):
    return f"C{sc['ch']:02d}_S{sc['n']:02d}_{sh['idx']+1:02d}"

def scenes_json():
    tl = build()
    lock = json.load(open(VOICE_LOCK)) if os.path.exists(VOICE_LOCK) else {}
    out = dict(project=TITLE_KH, project_en=TITLE_EN, source=SOURCE,
               language="km-KH", visual_style="2D Khmer cartoon (vector cut-out animation, clean outlines, soft cel shading)",
               resolution="1920x1080", fps=FPS, duration=round(tl["total"], 2),
               voice_engine="VoxCPM2 (openbmb/VoxCPM2, installed locally in ~/voxcpm-env), one locked reference voice per speaker",
               voices={k: dict(voice_id=f"voxcpm2:{k}", reference=f"audio/voices/{v['file']}", design=v.get("design"))
                       for k, v in lock.items()},
               scenes=[])
    shot_no = 0
    for sc in tl["scenes"]:
        sd = dict(scene=sc["n"], chapter=sc["ch"], title=sc["title_kh"], title_en=sc["title_en"],
                  source_section=sc["source"], start=round(sc["t0"], 2), duration=round(sc["t1"] - sc["t0"], 2),
                  location=sc["loc"], time_of_day=sc["tod"], music=sc["music"], ambience=sc["amb"],
                  characters=[c for c in sc["cast"]], shots=[])
        for sh in sc["shots"]:
            cam = sh.get("cam") or "wide"
            ins = cam.startswith("insert:")
            chars = [] if ins else [c for c in sc["cast"] if tl["stage"].vis(c, sh["t0"] + 0.3)
                                    and abs(tl["stage"].at(c, sh["t0"] + 0.3)[0]) < 900]
            if ins and sh.get("speaker"):
                chars = [sh["speaker"]]
            sd["shots"].append(dict(
                shot_id=shot_id(sc, sh, tl), file=f"visuals/shots/shot_{shot_no:03d}.mp4",
                storyboard=f"visuals/storyboard/shot_{shot_no:03d}.jpg", start=round(sh["t0"], 2), duration=round(sh["dur"], 2),
                camera=cam, characters=chars, location=(cam.split(":", 1)[1] if ins else sc["loc"]),
                action=sh.get("act") or sh.get("desc", ""), emotion=sh.get("emo", ""), dialogue=sh.get("kh"),
                dialogue_en=sh.get("en"), speaker=sh.get("speaker"),
                voice_id=f"voxcpm2:{voice_of(sh['speaker'])}" if sh.get("speaker") else None,
                audio_file=f"audio/dialogue/{sh['audio']}" if sh.get("audio") else None,
                background=f"{sc['loc']}:{sc['tod']}" if not ins else cam.split(":", 1)[1],
                foreground=("iron bars" if sc["loc"] == "visit" else ("over-the-shoulder " + cam.split(":")[1].split(">")[0]
                            if cam.startswith("ots:") else None)),
                sfx=sh.get("sfx", []), music=sc["music"],
                transition="fade_from_black" if sh["idx"] == 0 else ("fade_to_black" if sh is sc["shots"][-1] else "cut")))
            shot_no += 1
        out["scenes"].append(sd)
    json.dump(out, open(os.path.join(DOCS, "scenes.json"), "w"), ensure_ascii=False, indent=1)
    print("scenes.json written")

def screenplay_txt():
    lock = json.load(open(VOICE_LOCK)) if os.path.exists(VOICE_LOCK) else {}
    for lang in ("kh", "en"):
        L = [TITLE_KH if lang == "kh" else f"{TITLE_EN} ({TITLE_KH})",
             ("ស្គ្រីបភាពយន្តគំនូរជីវចល 2D ជាភាសាខ្មែរ" if lang == "kh" else "English reference translation of the Khmer screenplay"),
             "Source: " + SOURCE, "=" * 72]
        cur_ch = None
        for sc in SCENES:
            if sc["ch"] != cur_ch:
                cur_ch = sc["ch"]
                L += ["", "#" * 72, f"CHAPTER {cur_ch}", "#" * 72]
            L += ["", f"ឆាកទី {sc['n']} — {sc['title_kh']}  ({sc['title_en']})", f"Source: {sc['source']}",
                  f"Location: {sc['loc']} / {sc.get('tod','day')}   Music: {sc['music']}", "-" * 72]
            for it in sc["items"]:
                if it["type"] == "shot":
                    L += ["", f"[{it['kind'].upper()} · {it['cam']}] {it['desc']}"]
                else:
                    sp = it["sp"]
                    L += ["", f"CHARACTER_ID:\n{voice_of(sp).upper()}" + (f" ({sp})" if sp != voice_of(sp) else ""),
                          f"NAME:\n{CHARACTERS[sp]['kh']} ({CHARACTERS[sp]['en']})",
                          f"EMOTION:\n{it['emo'] or 'neutral'}", f"ACTION:\n{it['act'] or '—'}",
                          (f"DIALOGUE_KH:\n\"{it['kh']}\"" if lang == "kh" else f"DIALOGUE_EN:\n\"{it['en']}\""),
                          (f"(EN) {it['en']}" if lang == "kh" else f"(KH) {it['kh']}"),
                          f"VOICE_ID:\nvoxcpm2:{voice_of(sp)}   CAMERA: {it['cam'] or 'auto'}"]
        fn = "screenplay_khmer.txt" if lang == "kh" else "screenplay_english.txt"
        open(os.path.join(DOCS, fn), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("screenplays written")

# ───────────────────────────────────────────────────────────── assembly
def assemble():
    tl = build()
    shots_dir = os.path.join(FINAL, "visuals", "shots")
    lst = os.path.join(shots_dir, "concat.txt")
    with open(lst, "w") as f:
        for i in range(len(tl["shots"])):
            f.write(f"file 'shot_{i:03d}.mp4'\n")
    video = os.path.join(shots_dir, "_video_only.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video],
                   check=True)
    out = os.path.join(FINAL, OUT_MP4)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", video, "-i", os.path.join(ADIR, "mix.wav"),
                    "-i", os.path.join(FINAL, "subtitles_kh.srt"), "-i", os.path.join(FINAL, "subtitles_en.srt"),
                    "-map", "0:v", "-map", "1:a", "-map", "2", "-map", "3",
                    "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ac", "2",
                    "-ar", "48000", "-c:s", "mov_text", "-metadata:s:s:0", "language=khm",
                    "-metadata:s:s:0", "title=Khmer", "-metadata:s:s:1", "language=eng", "-metadata:s:s:1", "title=English",
                    "-metadata", f"title={TITLE_KH}", "-t", f"{tl['total']:.3f}", "-movflags", "+faststart", out], check=True)
    os.remove(video)
    print("wrote", out)

if __name__ == "__main__":
    for cmd in sys.argv[1:]:
        {"audio": build_audio, "docs": lambda: (subtitles(), scenes_json(), screenplay_txt()),
         "subs": subtitles, "assemble": assemble}[cmd]()
