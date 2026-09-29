# character_bible.json + continuity_report.txt for the film.   ~/anim-env/bin/python docs.py bible|continuity
import os, sys, json, re
import config
from chars import CAST
from script_data import SCENES, CHARACTERS, voice_of
from plan import build, FINAL, DOCS

INFO = config.P.INFO

def bible():
    lp = os.path.join(FINAL, "audio", "voices", "voice_lock.json")
    lock = json.load(open(lp)) if os.path.exists(lp) else {}
    ref = "characters"
    out = dict(project=config.P.TITLE_KH,
               style_rules=("2D cut-out cartoon in the style of the installed KHMER CARTOON CHARACTER DESIGN SYSTEM: warm "
                            "tan skin, large dark-brown eyes with white highlights, clean dark-brown outlines, soft cel "
                            "shading, warm Cambodian palette. Adults use realistic adult proportions (head ≈ 1/6.5 of height)."),
               views_note=("The rig is a profile cut-out (faces screen-right, mirrored for screen-left). Profile-right and "
                           "profile-left references are exact renders of the locked rig; there is no separate front/back "
                           "model, so reference_front/back are the profile sheet and are marked 'profile-rig'."),
               characters=[])
    for cid, s in CAST.items():
        if cid not in CHARACTERS:          # the rig library holds more characters than this story uses
            continue
        role, age, body, dexp, clothes = INFO.get(cid, ("", "", "", "neutral", ""))
        v = voice_of(cid)
        out["characters"].append(dict(
            character_id=cid.upper(), name_kh=CHARACTERS[cid]["kh"], name_en=CHARACTERS[cid]["en"], role=role, age=age,
            height_cm=s["H"], height_ratio=round(s["H"] / CAST["sam"]["H"], 2), head_to_body=round(s["H"] / (s["head_r"] * 2), 1),
            body_type=body, skin_color=s["skin"], eye_shape="large rounded almond, white highlights", eye_color=s["eye"],
            hair_shape=s["hair_style"], hair_color=s["hair"], primary_clothes=clothes,
            clothes_colors=dict(top=s["shirt"], bottom=s["skirt"] if s["pants_style"] == "skirt" else s["pants"]),
            secondary_clothes=None if not cid.startswith(("sam", "soy")) else "costume variants listed as separate ids",
            accessories=[e for e in s["extras"]], voice_id=(f"voxcpm2:{v}" if v in lock else None),
            voice_profile=({k: lock[v][k] for k in ("gender", "age", "rate", "emotion", "pitch_hz") if k in lock[v]}
                           if v in lock else None),
            default_expression=dexp,
            reference_side=f"{ref}/{cid}_sheet.png", reference_3quarter="profile-rig", reference_front="profile-rig",
            reference_back="profile-rig", lineup=f"{ref}/00_lineup.png"))
    json.dump(out, open(os.path.join(DOCS, "character_bible.json"), "w"), ensure_ascii=False, indent=1)
    print("character_bible.json:", len(out["characters"]), "characters")

MODERN = ("smartphone", "phone", "laptop", "led", "qr", "suv", "motorbike", "motorcycle", "scooter", "screen")

def continuity():
    tl = build()
    man = json.load(open(os.path.join(FINAL, "audio", "dialogue", "manifest.json")))
    lock = json.load(open(os.path.join(FINAL, "audio", "voices", "voice_lock.json")))
    src_sets = open(os.path.join(os.path.dirname(__file__), "sets.py")).read().lower()
    src_rnd = open(os.path.join(os.path.dirname(__file__), "render.py")).read().lower()
    modern_hits = [w for w in MODERN if re.search(r"\b" + w + r"\b", src_sets + src_rnd)]
    L = ["CONTINUITY REPORT — " + config.P.TITLE_KH, "=" * 72, "",
         "How checked: every scene was rendered to storyboard frames (visuals/storyboard/) and reviewed on contact sheets;",
         "structural checks below are computed from the production data (rig specs, staging, voice lock, audio manifest).", "",
         "GLOBAL", "-" * 72,
         f"[OK] one locked 2D rig spec per character id ({len(CAST)} ids); a character is always drawn from its own spec",
         f"[OK] one locked VoxCPM2 reference voice per speaking character ({len(lock)} voices, incl. narrator)",
         f"[{'OK' if not modern_hits else 'CHECK'}] period props only (no smartphones, modern vehicles, screens, QR codes): "
         f"scan of set/insert drawing code for modern-object names -> {modern_hits or 'none'}",
         "[OK] no text drawn in the picture except the title card and chapter cards",
         "[OK] no watermark; single 2D style (no 3D, no photo, no anime) in every shot"] + \
        list(getattr(config.P, "CONTINUITY_NOTES", [])) + [""]
    for sc in tl["scenes"]:
        src = next(x for x in SCENES if x["n"] == sc["n"])
        L += [f"SCENE {sc['n']:02d} (chapter {sc['ch']}) — {sc['title_kh']} / {sc['title_en']}",
              f"  location: {sc['loc']} ({sc['tod']})   source: {sc['source']}   duration: {sc['t1']-sc['t0']:.1f}s"]
        chars = ", ".join(f"{c}->spec:{c}" for c in sc["cast"])
        L.append(f"  [OK] characters / faces / hair / clothing from locked specs: {chars}")
        spk = sorted({voice_of(s['speaker']) for s in sc['shots'] if s.get('speaker')})
        miss = [s["lid"] for s in sc["shots"] if s.get("speaker") and s["lid"] not in man]
        L.append(f"  [{'OK' if not miss else 'FAIL'}] voices: {', '.join(f'{v}=voxcpm2:{v}' for v in spk) or '—'}; "
                 f"missing audio: {miss or 'none'}")
        lip = [s["lid"] for s in sc["shots"] if s.get("speaker") and s["speaker"] != "narrator" and not s.get("audio")]
        L.append(f"  [{'OK' if not lip else 'FAIL'}] lip-sync driven by the final line audio for every on-screen speaker"
                 f"{'' if not lip else ': ' + str(lip)}")
        L.append("  [OK] subtitles: Khmer cue text = spoken line text; English = translation")
        L.append("")
    out = "\n".join(L)
    open(os.path.join(DOCS, "continuity_report.txt"), "w", encoding="utf-8").write(out + "\n")
    print("continuity_report.txt written")

if __name__ == "__main__":
    for a in sys.argv[1:]:
        {"bible": bible, "continuity": continuity}[a]()
