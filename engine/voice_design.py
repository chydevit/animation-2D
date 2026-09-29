# Design candidate reference voices for every speaker of "ព្រះអាទិត្យថ្មីរះលើផែនដីចាស់" with VoxCPM2 voice
# design, then measure pitch so one can be locked per character. Run with ~/voxcpm-env/bin/python
# (A narrator can be reused from another project's voice lock: see project.NARRATOR_FROM_REUSE.)
import os, sys, json, time, random
import numpy as np, soundfile as sf, torch, librosa
from voxcpm import VoxCPM

import config
OUT = config.ep("audio", "voices", "candidates")
os.makedirs(OUT, exist_ok=True)

VOICES = config.P.VOICES
REF_TEXT = config.P.REF_TEXT
SEEDS = [int(x) for x in os.environ.get('SEEDS', '101,202').split(',')]

def f0_stats(path):
    y, sr = librosa.load(path, sr=16000)
    f0, vflag, _ = librosa.pyin(y, fmin=60, fmax=500, sr=sr)
    f0 = f0[~np.isnan(f0)]
    if len(f0) == 0:
        return dict(f0=0, f0sd=0, dur=len(y) / sr)
    return dict(f0=float(np.median(f0)), f0sd=float(np.std(f0)), dur=len(y) / sr,
                voiced=float(len(f0)) / max(1, len(vflag)))

if __name__ == "__main__":
    only = sys.argv[1:] or list(VOICES)
    model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)
    sr = model.tts_model.sample_rate
    sp = os.path.join(OUT, "stats.json")
    stats = json.load(open(sp)) if os.path.exists(sp) else {}
    for ch in only:
        for s in SEEDS:
            key = f"{ch}_s{s}"
            if key in stats and os.path.exists(os.path.join(OUT, key + ".wav")):
                continue
            random.seed(s); np.random.seed(s); torch.manual_seed(s)
            t = time.time()
            wav = model.generate(text=f"({VOICES[ch]}){REF_TEXT[ch]}", cfg_value=2.0, inference_timesteps=10)
            p = os.path.join(OUT, key + ".wav")
            sf.write(p, wav, sr)
            st = f0_stats(p); st["peak"] = float(np.abs(wav).max())
            stats[key] = st
            json.dump(stats, open(sp, "w"), indent=1)
            print(f"CAND {key}: dur={st['dur']:.2f}s f0={st['f0']:.0f}Hz sd={st['f0sd']:.0f} "
                  f"voiced={st.get('voiced',0):.2f} took={time.time()-t:.0f}s", flush=True)
    print("DONE", flush=True)
