# Lock one reference voice per speaking character: copy the chosen VoxCPM2 voice-design candidate to
# <episode>/audio/voices/<id>.wav + .txt and write voice_lock.json (the permanent voice profile).
# Selection (measured by voice_design.py): pitch fits the role's gender/age, stable pitch (low f0 sd), high voiced
# ratio (no whisper/silence), distinct from characters who share scenes. Roles in project.REUSE take an already-
# installed voice from another project's voice_lock.json instead (e.g. when every fresh design failed QA).
import os, json, shutil
import config

P = config.P
VD = config.ep("audio", "voices")
CAND = os.path.join(VD, "candidates")
REUSE_LOCK = config.ep(P.REUSE_LOCK) if getattr(P, "REUSE_LOCK", None) else None
if REUSE_LOCK and not os.path.exists(REUSE_LOCK):
    print("REUSE_LOCK not found, designing every voice:", REUSE_LOCK)
    REUSE_LOCK = None

def pick_best(ch, stats):
    male = P.PROFILE[ch][0] == "male"
    best = None
    for k, st in stats.items():
        if not k.startswith(ch + "_s"):
            continue
        f0, sd, v = st.get("f0", 0), st.get("f0sd", 999), st.get("voiced", 0)
        if f0 <= 0 or v < 0.55:
            continue
        lo, hi = (85, 165) if male else (170, 330)
        pen = 0 if lo <= f0 <= hi else 50 + min(abs(f0 - lo), abs(f0 - hi))
        score = pen + sd * 0.4 + (1 - v) * 40
        if best is None or score < best[0]:
            best = (score, k.split("_")[-1])
    return best[1] if best else None

if __name__ == "__main__":
    stats = json.load(open(os.path.join(CAND, "stats.json")))
    lock = {}
    old = json.load(open(REUSE_LOCK)) if REUSE_LOCK else {}
    reuse = dict(getattr(P, "REUSE", {})) if old else {}
    nar = getattr(P, "NARRATOR_FROM_REUSE", None)
    if old and nar:
        reuse["narrator"] = nar
    for ch, src_id in reuse.items():
        o = old[src_id]
        shutil.copy(os.path.join(os.path.dirname(REUSE_LOCK), o["file"]), os.path.join(VD, ch + ".wav"))
        open(os.path.join(VD, ch + ".txt"), "w", encoding="utf-8").write(o["text"])
        g, age, rate, emo = P.PROFILE.get(ch, ("", "", 1.0, ""))
        lock[ch] = dict(o, file=ch + ".wav", voice_id=f"voxcpm2:{ch}", speaker_id=ch, gender=g, age=age, rate=rate,
                        emotion=emo, reused_from=f"{os.path.relpath(REUSE_LOCK, config.EPISODE_DIR)}:{src_id}",
                        pronunciation="Khmer Unicode text; numbers spelled out in words in the TTS text")
        print(f"{ch:9s} <- installed voice '{src_id}'")
    for ch in P.VOICES:
        if ch in lock:
            continue
        seed = P.CHOICE.get(ch) or pick_best(ch, stats)
        key = f"{ch}_{seed}"
        shutil.copy(os.path.join(CAND, key + ".wav"), os.path.join(VD, ch + ".wav"))
        open(os.path.join(VD, ch + ".txt"), "w", encoding="utf-8").write(P.REF_TEXT[ch])
        st = stats[key]
        g, age, rate, emo = P.PROFILE[ch]
        lock[ch] = dict(file=ch + ".wav", text=P.REF_TEXT[ch], seed=int(seed[1:]) * 10 + 1, design=P.VOICES[ch],
                        source=key + ".wav", engine="VoxCPM2 (openbmb/VoxCPM2) voice design -> locked reference clone",
                        voice_id=f"voxcpm2:{ch}", speaker_id=ch, gender=g, age=age, rate=rate, emotion=emo,
                        pitch_hz=round(st["f0"]), pitch_sd=round(st["f0sd"]), cfg_value=2.0, inference_timesteps=10,
                        pronunciation="Khmer Unicode text; numbers spelled out in words in the TTS text")
        print(f"{ch:9s} <- {key}  f0={st['f0']:.0f}Hz sd={st['f0sd']:.0f} voiced={st.get('voiced', 0):.2f}")
    json.dump(lock, open(os.path.join(VD, "voice_lock.json"), "w"), ensure_ascii=False, indent=1)
    print("locked", len(lock), "voices")
