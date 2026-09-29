# Voice every screenplay line with VoxCPM2, cloning each speaker from its LOCKED reference clip
# (audio/voices/<speaker>.wav + .txt) so a character's voice never changes between scenes.
# Run with ~/voxcpm-env/bin/python.  Re-running only regenerates missing lines (or those passed as args).
import os, sys, json, time, random, re
import numpy as np, soundfile as sf, torch
from voxcpm import VoxCPM

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import config
from script_data import SCENES, voice_of

FINAL = config.EPISODE_DIR
VDIR = os.path.join(FINAL, "audio", "voices")
LDIR = os.path.join(FINAL, "audio", "dialogue")
os.makedirs(LDIR, exist_ok=True)
MANIFEST = os.path.join(LDIR, "manifest.json")
VOICE_LOCK = os.path.join(VDIR, "voice_lock.json")

def khmer_len(s):
    # count "spoken" characters (ignore punctuation / spaces)
    return len(re.sub(r"[\s។៖!?.,…'\"“”—\-]", "", s))

def trim(wav, sr, thr=0.012):
    a = np.abs(wav)
    win = int(sr * 0.02)
    env = np.convolve(a, np.ones(win) / win, mode="same")
    idx = np.where(env > thr)[0]
    if len(idx) == 0:
        return wav
    s0 = max(0, idx[0] - int(sr * 0.04))
    s1 = min(len(wav), idx[-1] + int(sr * 0.08))
    out = wav[s0:s1].copy()
    f = int(sr * 0.012)
    out[:f] *= np.linspace(0, 1, f)
    out[-f:] *= np.linspace(1, 0, f)
    return out

def longest_gap(wav, sr, thr=0.01):
    win = int(sr * 0.02)
    env = np.convolve(np.abs(wav), np.ones(win) / win, mode="same") > thr
    best = cur = 0
    for v in env[::win]:
        cur = 0 if v else cur + 1
        best = max(best, cur)
    return best * 0.02

def lines():
    out, k = [], 0
    for s in SCENES:
        for it in s["items"]:
            if it["type"] == "line":
                k += 1
                out.append(dict(id=f"L{k:03d}", scene=s["n"], sp=it["sp"], tts=it["tts"], kh=it["kh"]))
    return out

if __name__ == "__main__":
    lock = json.load(open(VOICE_LOCK))
    todo_ids = set(sys.argv[1:])
    man = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}
    model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)
    sr = model.tts_model.sample_rate
    for ln in lines():
        lid = ln["id"]
        path = os.path.join(LDIR, f"{lid}_{ln['sp']}.wav")
        if not todo_ids and lid in man and os.path.exists(path) and man[lid].get("tts", ln["tts"]) == ln["tts"] \
                and voice_of(man[lid]["sp"]) == voice_of(ln["sp"]):
            continue
        if todo_ids and lid not in todo_ids:
            continue
        v = lock[voice_of(ln["sp"])]
        ref = os.path.join(VDIR, v["file"])
        best = None
        for attempt in range(3):
            seed = v["seed"] + attempt * 7919
            random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
            t = time.time()
            wav = model.generate(text=ln["tts"], reference_wav_path=ref, cfg_value=2.0, inference_timesteps=10)
            wav = trim(np.asarray(wav, dtype=np.float32), sr)
            dur = len(wav) / sr
            cps = khmer_len(ln["tts"]) / max(dur, 0.1)
            gap = longest_gap(wav, sr)
            exp = max(0.8, khmer_len(ln["tts"]) / 13.0)
            ok = (6.0 <= cps <= 22.0) and gap < 1.1 and np.abs(wav).max() > 0.05 and dur < exp * 2.2 + 1.0
            score = abs(cps - 13.0) + (5 if gap >= 1.3 else 0)
            print(f"{lid} {ln['sp']:8s} try{attempt} dur={dur:5.2f}s cps={cps:5.1f} gap={gap:.2f} "
                  f"{'OK' if ok else 'RETRY'} ({time.time()-t:.0f}s)", flush=True)
            if best is None or score < best[0]:
                best = (score, wav, dur, cps, gap, seed, ok)
            if ok:
                break
        _, wav, dur, cps, gap, seed, ok = best
        peak = np.abs(wav).max()
        wav = wav / peak * 0.89
        sf.write(path, wav, sr)
        man[lid] = dict(file=os.path.basename(path), sp=ln["sp"], scene=ln["scene"], dur=round(dur, 3), tts=ln["tts"],
                        cps=round(cps, 2), gap=round(gap, 2), seed=seed, qa_ok=bool(ok), sr=sr)
        json.dump(man, open(MANIFEST, "w"), indent=1, ensure_ascii=False)
        # free the MPS allocator cache after every line (it otherwise grows until the machine swaps)
        import gc; gc.collect()
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
        done_now = globals().get("_done_now", 0) + 1; globals()["_done_now"] = done_now
        if done_now >= int(os.environ.get("TTS_BATCH", "20")):
            print("BATCH_END", flush=True); sys.exit(3)
    tot = sum(m["dur"] for m in man.values())
    print(f"DONE {len(man)} lines, {tot/60:.1f} min of speech; flagged: "
          f"{[k for k,m in man.items() if not m['qa_ok']]}", flush=True)
