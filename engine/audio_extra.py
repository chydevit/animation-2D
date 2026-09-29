"""audio_extra.py -- extra procedural music cues, ambiences and SFX for "ព្រះអាទិត្យថ្មីរះលើផែនដីចាស់".
Builds on audio_synth.py (same synthesis helpers; everything is generated locally, no samples).
"""
import numpy as np
import audio_synth as AS
from audio_synth import (SR, TAU, _rng, _n, _t, lp, hp, bp, pan, _add, _srand, _fade, _env_ar, _modes, _noise, _brown,
                         _thump, _burst, _clink, _creak, _wind, _birds, _babble, _engine_pass, _lowhit, reverb, _finish,
                         _trim_tail)

# ───────────────────────────────────────────── music cues (Cambodian-inspired: roneat, khloy, skor, ching)
C = AS._CUES
C["city"] = dict(C["opening"], bpm=96, root=74, plan=["roneat", "roneat", "both", "roneat"], skor="workers",
                 ching="offbeat", gains=dict(roneat=0.50, khloy=0.30, pad=0.08, skor=0.30, ching=0.05))
C["hardship"] = dict(C["family_sad"], root=64, bpm=58, gains=dict(khloy=0.45, pad=0.16, arp=0.10))
C["threat"] = dict(C["tension_low"])
C["temple"] = dict(C["ending"], bpm=60, root=65, plan=["khloy"], ching="bar", skor=None,
                   gains=dict(khloy=0.45, roneat=0.2, pad=0.16, arp=0.10, ching=0.04))
C["confront"] = C["confront"]
C["prison"] = dict(C["police"], hits=False, gains=dict(sparse=0.55, pad=0.10, drone=0.10, skor=0.12))
C["hope"] = dict(C["opening"], bpm=76, root=67, plan=["khloy", "both", "roneat", "both"],
                 gains=dict(roneat=0.42, khloy=0.40, pad=0.12, skor=0.18, ching=0.04))
C["workers"] = C["workers"]
C["neutral"] = dict(C["tension_low"], skor=None, gains=dict(sparse=0.55, pad=0.12, drone=0.06))
C["tragedy"] = dict(C["tension_low"], skor=None, sparse=(45, 0.08), gains=dict(sparse=0.25, pad=0.10, drone=0.08))
C["lowest"] = dict(C["family_sad"], bpm=54, root=62, gains=dict(khloy=0.38, pad=0.14, arp=0.08))
C["reflect"] = dict(C["family_sad"], bpm=60, root=67, gains=dict(khloy=0.40, pad=0.16, arp=0.14))
C["sunrise"] = dict(C["ending"])

def music(cue, duration, seed=0):
    return AS.music(cue, duration, seed)

# ───────────────────────────────────────────── ambiences
AMB_ALIAS = {"country": "home", "street": "street", "temple": "home", "house": "office", "house_poor": "home",
             "night": "night", "crowd_room": "office", "clinic": "night", "hospital": "office", "office": "office"}

def _rain(n, rng, heavy=1.0):
    nz = np.stack([rng.standard_normal(n), rng.standard_normal(n)], 1)
    y = bp(nz, 800, 7000) * 0.5 + lp(nz, 600) * 0.3
    y *= (0.8 + 0.2 * _srand(n, 0.3, rng))[:, None]
    drops = nz * (rng.random((n, 2)) < 0.002 * heavy)
    y += bp(drops, 2000, 8000) * 1.2
    return y * heavy

def ambience(kind, duration, seed=0):
    if kind in AMB_ALIAS:
        return AS.ambience(AMB_ALIAS[kind], duration, seed)
    rng = _rng(seed, "amb2", kind)
    N = _n(duration)
    NB = N + _n(1.5)
    out = np.zeros((NB, 2))
    if kind in ("rain_in", "rain_out"):
        out += _rain(NB, rng, 1.0 if kind == "rain_out" else 0.7)
        if kind == "rain_in":
            out = lp(out, 3500)
        t = rng.uniform(3, 10)
        while t < NB / SR:
            m = _n(4.0)
            th = lp(_brown(m, rng), 120) * _env_ar(m, 0.4, 2.5) * 2.5
            _add(out, pan(th, rng.uniform(-0.5, 0.5)), _n(t))
            t += rng.uniform(12, 25)
        target = -15.0
    elif kind == "factory":
        base = AS.ambience("garage", duration + 1.5, seed)[:NB]
        out[: len(base)] += base
        tt = _t(NB)
        hum = (np.sin(TAU * 100 * tt) * 0.3 + np.sin(TAU * 50 * tt) * 0.5 + 0.2 * np.sin(TAU * 150 * tt))
        hum *= 0.25 * (0.85 + 0.15 * np.sin(TAU * 0.7 * tt))
        belt = bp(rng.standard_normal(NB), 300, 1200) * (0.5 + 0.5 * np.sin(TAU * 3.1 * tt) ** 8) * 0.25
        out += pan(hum + belt, 0)
        target = -13.0
    elif kind == "prison":
        out += lp(np.stack([_brown(NB, rng), _brown(NB, rng)], 1), 250) * 0.3
        ev = np.zeros((NB, 2))
        t = rng.uniform(2, 6)
        while t < NB / SR:
            k = _modes(_n(1.5), np.array([180, 410, 690, 1130]) * rng.uniform(.95, 1.05), [.6, .4, .3, .2], [1, .6, .4, .2])
            _add(ev, pan(lp(k, 1500) * 0.25, rng.uniform(-0.8, 0.8)), _n(t))
            t += rng.uniform(6, 14)
        out += reverb(ev, rt=2.5, wet=0.7, damp=2500, tail=False, seed=7)
        target = -17.0
    elif kind == "train":
        tt = _t(NB)
        rum = lp(np.stack([_brown(NB, rng), _brown(NB, rng)], 1), 160) * 0.6
        period = 0.42
        clack = np.zeros(NB)
        t = 0.0
        while t < NB / SR:
            _add(clack, _thump(_n(0.12), 180, 120, 0.02, rng, 0.8, 2500) * 0.6, _n(t))
            _add(clack, _thump(_n(0.12), 170, 110, 0.02, rng, 0.8, 2500) * 0.5, _n(t + 0.11))
            t += period
        out += rum + pan(clack, 0.1)
        target = -13.0
    elif kind == "river":
        out += AS.ambience("night", duration + 1.5, seed)[:NB] * 0.8
        w = bp(np.stack([rng.standard_normal(NB), rng.standard_normal(NB)], 1), 200, 1500)
        out += w * (0.25 + 0.2 * _srand(NB, 0.4, rng))[:, None]
        target = -15.0
    elif kind == "market":
        out += AS.ambience("street", duration + 1.5, seed)[:NB]
        out += lp(_babble(NB, rng, 16, rate=(3, 6)), 2200) * 0.5
        target = -12.0
    else:
        return AS.ambience("office", duration, seed)
    y = hp(out[:N], 40)
    y = _fade(y, 1.0, 1.0)
    return _finish(y, rms=target, max_peak=-1.0)

# ───────────────────────────────────────────── SFX
SFX_ALIAS = {"footsteps_dirt": "footsteps_sandal", "gavel": "desk_knock", "traffic_old": "car_depart"}

def _bell(f0, dec, partials=(1, 2.76, 5.4, 8.9), amps=(1, .5, .3, .15), n_s=3.0, rng=None):
    n = _n(n_s)
    y = _modes(n, np.array(partials) * f0, np.array([dec, dec * .6, dec * .4, dec * .25]), list(amps))
    y[:_n(0.001)] *= np.linspace(0, 1, _n(0.001))
    return y

def _raw(name, rng):
    if name == "birds_morning" or name == "birds_city":
        n = _n(5.0 if name == "birds_morning" else 3.5)
        y = _birds(n, rng) * (1.0 if name == "birds_morning" else 0.5)
        return y, (0.6, 0.2, 7000)
    if name == "hoe_dirt":
        n = _n(3.0)
        y = np.zeros(n)
        for i in range(3):
            _add(y, _thump(_n(0.4), 90, 60, 0.05, rng, 0.9, 900) + bp(rng.standard_normal(_n(0.4)), 600, 3000)
                 * np.exp(-_t(_n(0.4)) / 0.06) * 0.6, _n(0.1 + i * 0.95))
        return pan(y, 0), (0.4, 0.1, 5000)
    if name == "train_run":
        y = ambience("train", 5.5, int(rng.integers(0, 99)))
        t = _t(_n(1.4))
        wh = (np.sin(TAU * 520 * t) + 0.6 * np.sin(TAU * 650 * t) + 0.3 * np.sin(TAU * 780 * t)) * _env_ar(len(t), 0.1, 0.4)
        _add(y, pan(lp(wh, 3000) * 0.12, 0.4), _n(0.4))
        return y, (1.4, 0.2, 4000)
    if name == "cyclo_bell":
        y = np.zeros(_n(1.4))
        for i in range(2):
            _add(y, _bell(2350, 0.35, (1, 1.51, 2.63, 3.9), (1, .6, .35, .2), 1.0), _n(0.02 + i * 0.22))
        return pan(y, 0.2), (0.5, 0.15, 8000)
    if name == "cyclo_chain":
        n = _n(3.0)
        y = np.zeros(n)
        t = 0.0
        while t < 2.9:
            _add(y, _clink(rng, rng.uniform(2500, 4000), 0.015) * 0.2, _n(t))
            t += rng.uniform(0.05, 0.09)
        y += lp(rng.standard_normal(n), 300) * 0.05
        return pan(hp(y, 300), 0), (0.3, 0.1, 6000)
    if name == "thunder_far":
        n = _n(5.0)
        y = lp(_brown(n, rng), 140) * _env_ar(n, 0.3, 3.0) * 3
        return pan(y, rng.uniform(-0.4, 0.4)), (2.0, 0.3, 1500)
    if name == "drip":
        n = _n(3.0)
        y = np.zeros(n)
        for i in range(4):
            m = _n(0.15)
            f = np.linspace(1400, 2400, m)
            _add(y, np.sin(TAU * np.cumsum(f) / SR) * np.exp(-_t(m) / 0.03) * 0.5, _n(0.2 + i * 0.7))
        return pan(y, -0.2), (0.8, 0.3, 6000)
    if name == "rain_heavy":
        n = _n(5.0)
        y = _rain(n, rng, 1.0)
        return _fade(y, 0.8, 0.8), (0.3, 0.05, 8000)
    if name in ("cloth_rustle", "broom"):
        n = _n(2.5)
        y = np.zeros(n)
        for i in range(5 if name == "broom" else 4):
            m = _n(0.35)
            s = bp(rng.standard_normal(m), 1500 if name == "broom" else 900, 7000) * np.sin(np.pi * np.linspace(0, 1, m)) ** 2
            _add(y, s * 0.5, _n(0.1 + i * 0.45))
        return pan(y, 0), (0.3, 0.1, 7000)
    if name == "crickets":
        return AS.ambience("night", 4.0, int(rng.integers(0, 99))) * 0.8, (0.2, 0.05, 8000)
    if name == "temple_bell":
        y = _bell(310, 2.6, (1, 2.32, 4.2, 6.8), (1, .45, .25, .1), 5.0)
        return pan(y, -0.3), (2.2, 0.35, 4000)
    if name == "dish_wash":
        n = _n(2.5)
        y = bp(rng.standard_normal(n), 500, 4000) * (0.3 + 0.7 * _srand(n, 3, rng)) * 0.3
        for i in range(3):
            _add(y, _clink(rng, rng.uniform(1800, 3000), 0.1) * 0.4, _n(0.3 + i * 0.7))
        return pan(y, 0.1), (0.5, 0.2, 6000)
    if name == "clock_tick":
        n = _n(4.0)
        y = np.zeros(n)
        for i in range(8):
            _add(y, _clink(rng, 3200 if i % 2 else 2700, 0.01) * 0.5, _n(0.05 + i * 0.5))
        return pan(y, 0.3), (0.6, 0.2, 7000)
    if name == "cup_break":
        n = _n(1.5)
        y = np.zeros(n)
        _add(y, _thump(_n(0.2), 400, 200, 0.02, rng, 1.0, 6000) * 0.5, 0)
        for i in range(12):
            _add(y, _clink(rng, rng.uniform(2500, 6000), rng.uniform(0.02, 0.08)) * rng.uniform(0.3, 0.9),
                 _n(rng.uniform(0, 0.6)))
        return pan(y, 0), (0.7, 0.25, 7000)
    if name == "bell_small":
        y = np.zeros(_n(2.0))
        for i in range(3):
            _add(y, _bell(1850, 0.5, (1, 2.1, 3.3, 4.9), (1, .5, .3, .15), 1.0) * 0.7, _n(0.02 + i * 0.16))
        return pan(y, 0.3), (0.8, 0.2, 7000)
    if name == "metal_door":
        n = _n(3.5)
        y = _modes(n, np.array([95, 210, 380, 590, 870]) * rng.uniform(.98, 1.02), [1.2, .9, .6, .4, .3], [1, .7, .5, .3, .2])
        y += _thump(n, 120, 60, 0.2, rng, 1.0, 1500) * 0.8
        y[:_n(0.001)] *= np.linspace(0, 1, _n(0.001))
        return pan(lp(y, 5000) * 0.9, 0), (2.4, 0.4, 3000)
    if name == "room_tone":
        n = _n(3.0)
        return pan(lp(_brown(n, rng), 200) * 0.2, 0), (0.3, 0.05, 3000)
    if name == "scuffle":
        n = _n(2.8)
        y = np.zeros(n)
        for i in range(7):
            _add(y, _thump(_n(0.3), 90, 55, 0.05, rng, 0.9, 700) * rng.uniform(0.3, 0.7), _n(rng.uniform(0, 2.4)))
            _add(y, bp(rng.standard_normal(_n(0.25)), 400, 3000) * np.exp(-_t(_n(0.25)) / 0.08) * 0.3,
                 _n(rng.uniform(0, 2.4)))
        return pan(lp(y, 2500), 0), (1.2, 0.35, 2500)
    if name == "baton_bars":
        n = _n(1.6)
        y = np.zeros(n)
        for i in range(3):
            _add(y, _modes(_n(0.8), np.array([640, 1510, 2790]) * rng.uniform(.98, 1.02), [.3, .2, .1], [1, .6, .3]),
                 _n(0.02 + i * 0.3))
        return pan(y, 0.2), (1.4, 0.3, 4000)
    if name == "car_brake":
        n = _n(1.6)
        t = _t(n)
        f = np.interp(t, [0, 1.2, 1.6], [2100, 1700, 1500])
        y = (np.sin(TAU * np.cumsum(f) / SR) + 0.5 * np.sin(TAU * np.cumsum(f * 1.5) / SR)) * 0.25
        y += bp(rng.standard_normal(n), 1500, 5000) * 0.35
        y *= _env_ar(n, 0.05, 0.3)
        return pan(lp(y, 6000), 0.3), (0.8, 0.2, 5000)
    if name == "thud":
        y = _lowhit(1)[: _n(1.5)] * 0.9
        return pan(y, 0), (0.8, 0.2, 2500)
    if name in ("sack_drop", "crate"):
        n = _n(1.2)
        y = _thump(n, 80 if name == "sack_drop" else 140, 50, 0.08, rng, 0.9, 900)
        if name == "crate":
            y += 0.4 * _modes(n, [220, 470, 900], [.08, .05, .03], [1, .6, .3])
        y += bp(rng.standard_normal(n), 800, 4000) * np.exp(-_t(n) / 0.1) * 0.3
        return pan(y, 0), (0.7, 0.2, 4000)
    if name == "vat_stir" or name == "water_oar" or name == "water_pour":
        n = _n(3.5)
        t = _t(n)
        rate = {"vat_stir": 0.8, "water_oar": 0.6, "water_pour": 0}[name]
        env = 0.4 + 0.6 * (np.sin(TAU * rate * t) ** 2 if rate else 1.0)
        y = bp(rng.standard_normal(n), 250, 2500) * env * 0.5
        y += bp(rng.standard_normal(n) * (rng.random(n) < 0.004), 800, 4000) * 1.5
        return pan(lp(y, 4000), 0), (0.6, 0.2, 4000)
    if name == "gate_shut":
        n = _n(2.5)
        y = bp(rng.standard_normal(n), 400, 3000) * np.clip(1 - _t(n) / 0.8, 0, 1) * 0.3
        clang = _modes(_n(1.6), np.array([160, 380, 720, 1150]) * rng.uniform(.98, 1.02), [.8, .6, .4, .3], [1, .7, .5, .3])
        _add(y, clang, _n(0.8))
        return pan(y, 0.2), (1.8, 0.3, 3500)
    if name == "market_amb":
        return ambience("market", 4.5, int(rng.integers(0, 99))), (0.3, 0.05, 5000)
    if name == "dog_far":
        n = _n(1.6)
        y = np.zeros(n)
        for i in range(2):
            m = _n(0.18)
            tt = _t(m)
            f = np.interp(tt, [0, 0.05, 0.18], [380, 520, 300])
            b = AS._saw(f, m) * _env_ar(m, 0.01, 0.12)
            _add(y, bp(b, 400, 2000), _n(0.1 + i * 0.35))
        return pan(lp(y, 2000) * 0.5, -0.5), (2.0, 0.6, 2000)
    if name == "factory_hum":
        return ambience("factory", 4.0, int(rng.integers(0, 99))), (0.2, 0.05, 4000)
    raise ValueError(name)

def sfx(name, seed=0):
    name = SFX_ALIAS.get(name, name)
    if name in AS.SFX_NAMES:
        return AS.sfx(name, seed)
    rng = _rng(seed, "sfx2", name)
    y, (rt, wet, damp) = _raw(name, rng)
    if y.ndim == 1:
        y = pan(y, 0)
    y = reverb(y, rt=rt, wet=wet, damp=damp, predelay=0.01, tail=True, seed=11)
    y = lp(hp(y, 30), 11000)
    y = _trim_tail(y, -60.0)
    return _finish(y, peak=-6.0)

if __name__ == "__main__":
    import soundfile as sf, os, sys
    out = sys.argv[1] if len(sys.argv) > 1 else "audio_tests"
    os.makedirs(out, exist_ok=True)
    names = ["birds_morning", "hoe_dirt", "train_run", "cyclo_bell", "cyclo_chain", "thunder_far", "drip", "rain_heavy",
             "cloth_rustle", "crickets", "temple_bell", "broom", "dish_wash", "clock_tick", "cup_break", "bell_small",
             "gavel", "metal_door", "room_tone", "scuffle", "baton_bars", "car_brake", "thud", "sack_drop", "vat_stir",
             "crate", "gate_shut", "water_oar", "market_amb", "dog_far", "water_pour", "factory_hum", "birds_city",
             "footsteps_dirt", "traffic_old"]
    for nm in names:
        x = sfx(nm, 1)
        assert np.all(np.isfinite(x)) and np.abs(x).max() < 1.0, nm
        print(f"sfx {nm:16s} {len(x)/SR:5.2f}s peak {np.abs(x).max():.2f}")
    for k in ("rain_in", "factory", "prison", "train", "river", "market", "country"):
        x = ambience(k, 6, 1)
        print(f"amb {k:10s} rms {AS.loudness_rms_db(x):.1f} dB")
    for cue in ("city", "hardship", "temple", "prison", "hope", "neutral", "tragedy", "lowest", "reflect", "sunrise"):
        x = music(cue, 8, 1)
        print(f"music {cue:10s} peak {np.abs(x).max():.2f}")
