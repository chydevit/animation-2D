"""
audio_synth.py -- procedural music, ambience and SFX for "រឿងថៅកែចិត្តចោរ".

Everything is synthesized from scratch with numpy/scipy (no samples, no network).
Sample rate 48 kHz; every public function returns float32 stereo arrays (N, 2),
deterministic for a given `seed`.

Public API
----------
music(cue, duration, seed=0)      cues: opening, tension_low, family_sad, confront,
                                        workers, police, ending          (-3 dBFS peak)
ambience(kind, duration, seed=0)  kinds: garage, office, home, street, night
                                                                  (about -12..-14 dBFS RMS)
sfx(name, seed=0)                 see SFX_NAMES                    (-6 dBFS peak)
loudness_rms_db(x), fit(x, duration)
"""
from __future__ import annotations

import functools
import os
import sys
import time
import zlib

import numpy as np
from scipy import signal as sps

SR = 48000
TAU = 2 * np.pi

MUSIC_CUES = ("opening", "tension_low", "family_sad", "confront", "workers", "police", "ending")
AMBIENCE_KINDS = ("garage", "office", "home", "street", "night")
SFX_NAMES = (
    "footsteps_wood", "footsteps_concrete", "footsteps_sandal", "paper_page", "pen_write",
    "chair_wood", "desk_knock", "car_arrive", "car_door", "car_depart", "tool_clank",
    "hammer_metal", "coins", "banknotes", "police_whistle", "jeep_arrive", "crowd_murmur",
    "gasp_room", "door_wood", "whoosh_soft", "heartbeat_soft",
)


# ----------------------------------------------------------------------------
# basic DSP helpers
# ----------------------------------------------------------------------------
def _rng(seed, *keys):
    h = zlib.crc32("|".join(str(k) for k in keys).encode())
    return np.random.default_rng([int(seed) & 0xFFFFFFFF, h])


def _n(sec):
    return max(0, int(round(sec * SR)))


def _t(n):
    return np.arange(n) / SR


def _db2a(db):
    return 10.0 ** (db / 20.0)


@functools.lru_cache(maxsize=512)
def _butter(order, fc, btype):
    return sps.butter(order, fc, btype=btype, fs=SR, output="sos")


def lp(x, fc, order=2):
    return sps.sosfilt(_butter(order, float(min(fc, SR * 0.45)), "lowpass"), x, axis=0)


def hp(x, fc, order=2):
    return sps.sosfilt(_butter(order, float(fc), "highpass"), x, axis=0)


def bp(x, lo, hi, order=2):
    hi = min(hi, SR * 0.45)
    return sps.sosfilt(_butter(order, (float(lo), float(hi)), "bandpass"), x, axis=0)


def peaking(x, f0, gain_db, q=0.7):
    A = 10 ** (gain_db / 40)
    w = TAU * f0 / SR
    al = np.sin(w) / (2 * q)
    b = np.array([1 + al * A, -2 * np.cos(w), 1 - al * A])
    a = np.array([1 + al / A, -2 * np.cos(w), 1 - al / A])
    return sps.lfilter(b / a[0], a / a[0], x, axis=0)


def _smooth(x, tau):
    """one-pole smoother starting at x[0]."""
    a = 1 - np.exp(-1.0 / (tau * SR))
    y, _ = sps.lfilter([a], [1, a - 1], x, zi=[(1 - a) * x[0]])
    return y


def pan(m, p=0.0):
    """constant-power pan; p in [-1, 1] (scalar or per-sample array)."""
    ang = (np.clip(p, -1, 1) + 1) * np.pi / 4
    return np.stack([m * np.cos(ang), m * np.sin(ang)], axis=1)


def _add(buf, sig, i0):
    i0 = int(i0)
    if i0 >= len(buf) or len(sig) == 0:
        return
    if i0 < 0:
        sig = sig[-i0:]
        i0 = 0
    n = min(len(sig), len(buf) - i0)
    buf[i0:i0 + n] += sig[:n]


def _srand(n, rate, rng, lo=0.0, hi=1.0):
    """smooth random curve (smoothstep interpolation of random points at `rate` Hz)."""
    k = int(n / SR * rate) + 3
    p = rng.uniform(lo, hi, k)
    x = np.arange(n) * (rate / SR)
    i = x.astype(np.int64)
    f = x - i
    s = f * f * (3 - 2 * f)
    return p[i] + (p[i + 1] - p[i]) * s


def _ramp(n):
    return 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, max(n, 1)))


def _fade(x, fin, fout):
    n = len(x)
    a = min(_n(fin), n // 2)
    b = min(_n(fout), n // 2)
    if a:
        x[:a] *= _ramp(a)[:, None] if x.ndim == 2 else _ramp(a)
    if b:
        x[n - b:] *= _ramp(b)[::-1, None] if x.ndim == 2 else _ramp(b)[::-1]
    return x


def _env_ar(n, att, rel):
    e = np.ones(n)
    a = min(_n(att), n)
    r = min(_n(rel), n - a)
    if a:
        e[:a] = _ramp(a)
    if r:
        e[n - r:] *= _ramp(r)[::-1]
    return e


def _modes(n, freqs, decays, amps, phase0=True):
    t = _t(n)
    y = np.zeros(n)
    for f, d, a in zip(freqs, decays, amps):
        if f >= SR * 0.45:
            continue
        y += a * np.sin(TAU * f * t) * np.exp(-t / d)
    return y


def _noise(n, rng):
    return rng.standard_normal(n)


def _brown(n, rng, leak=0.998):
    y = sps.lfilter([1.0], [1.0, -leak], rng.standard_normal(n))
    y = hp(y, 15)
    return y / (np.std(y) + 1e-12)


def _mtof(m):
    return 440.0 * 2.0 ** ((np.asarray(m, dtype=float) - 69.0) / 12.0)


def _saw(f, n, ph0=0.0):
    ph = (np.cumsum(np.broadcast_to(f, (n,)) / SR) + ph0) % 1.0
    return 2 * ph - 1


# --------------------------- reverb -----------------------------------------
@functools.lru_cache(maxsize=24)
def _ir(rt, damp, predelay, seed):
    r = np.random.default_rng(seed + 9173)
    L = _n(rt * 1.1)
    t = _t(L)
    env = np.exp(-6.91 * t / rt)
    raw = r.standard_normal((L, 2)) * env[:, None]
    a = lp(raw, damp, 2)
    b = lp(raw, damp * 0.35, 2)
    w = np.clip(t / rt, 0, 1)[:, None]
    ir = a * (1 - w) + b * w
    k = _n(0.004)
    ir[:k] *= _ramp(k)[:, None]
    ir = np.concatenate([np.zeros((_n(predelay), 2)), ir])
    ir /= np.sqrt(np.sum(ir ** 2, axis=0, keepdims=True)) + 1e-12
    return ir


def reverb(x, rt=1.2, wet=0.2, damp=6000.0, predelay=0.015, tail=True, seed=0):
    if x.ndim == 1:
        x = pan(x, 0)
    ir = _ir(float(rt), float(damp), float(predelay), int(seed))
    if tail:
        x = np.concatenate([x, np.zeros((len(ir), 2))])
    w = sps.oaconvolve(x, ir, axes=0)[: len(x)]
    return x + wet * w


# --------------------------- levels / output --------------------------------
def loudness_rms_db(x) -> float:
    x = np.asarray(x, dtype=np.float64)
    return float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12))


def peak_db(x) -> float:
    return float(20 * np.log10(np.max(np.abs(x)) + 1e-12))


def _softlimit(x, lim):
    k = 0.8 * lim
    ax = np.abs(x)
    over = ax > k
    y = x.copy()
    y[over] = np.sign(x[over]) * (k + (lim - k) * np.tanh((ax[over] - k) / (lim - k)))
    return y


def _finish(x, peak=None, rms=None, max_peak=-1.0):
    x = np.nan_to_num(np.asarray(x, dtype=np.float64))
    if x.ndim == 1:
        x = pan(x, 0)
    x = x - x.mean(axis=0, keepdims=True)
    if peak is not None:
        p = np.max(np.abs(x))
        if p > 0:
            x *= _db2a(peak) / p
    if rms is not None:
        r = np.sqrt(np.mean(x ** 2))
        if r > 0:
            x *= _db2a(rms) / r
        if np.max(np.abs(x)) > _db2a(max_peak):
            x = _softlimit(x, _db2a(max_peak))
    return x.astype(np.float32)


def _trim_tail(x, thresh_db=-65.0, fade=0.05):
    a = np.max(np.abs(x), axis=1)
    thr = np.max(a) * _db2a(thresh_db)
    idx = np.nonzero(a > thr)[0]
    end = min(len(x), (idx[-1] if len(idx) else len(x)) + _n(fade))
    x = x[:end].copy()
    k = min(_n(fade), len(x))
    x[len(x) - k:] *= _ramp(k)[::-1, None]
    return x


def fit(x, duration) -> np.ndarray:
    """pad with silence or trim (with a 10 ms fade) to exactly `duration` seconds."""
    x = np.asarray(x, dtype=np.float32)
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    n = _n(duration)
    if len(x) >= n:
        y = x[:n].copy()
        k = min(_n(0.01), n)
        if len(x) > n and k:
            y[n - k:] *= _ramp(k)[::-1, None].astype(np.float32)
        return y
    return np.concatenate([x, np.zeros((n - len(x), 2), np.float32)])


# ============================================================================
# MUSIC
# ============================================================================
SCALES = {"major": [0, 2, 4, 7, 9], "minor": [0, 3, 5, 7, 10]}


def _dm(root, scale, d):
    """scale degree -> midi. degree 5 == root, 0..4 the octave below."""
    d = int(d)
    return root + 12 * (d // 5 - 1) + scale[d % 5]


# --- instrument voices (cached one-shots) -----------------------------------
_CACHE: dict = {}


def _roneat_note(midi, muted=False, var=0):
    key = ("ron", round(midi * 100), muted, var)
    if key in _CACHE:
        return _CACHE[key]
    r = np.random.default_rng(zlib.crc32(repr(key).encode()))
    f = float(_mtof(midi))
    d = float(np.clip(0.9 * (440.0 / f) ** 0.4, 0.3, 1.8))
    if muted:
        d *= 0.28
    n = _n(min(d * 5.0, 4.5) + 0.03)
    t = _t(n)
    y = np.zeros(n)
    for ra, am, de in ((1.0, 1.0, d), (3.93, 0.30, d / 3.2), (9.21, 0.10, d / 8.0)):
        fr = f * ra * (1 + r.uniform(-0.003, 0.003))
        if fr > 8500:
            continue
        y += am * np.sin(TAU * fr * t) * np.exp(-t / de)
    nc = _n(0.012)
    click = lp(r.standard_normal(nc), 3000 if muted else 5000) * np.exp(-_t(nc) / 0.0015)
    y[:nc] += (0.35 if muted else 0.22) * click
    if muted:
        y = lp(y, 2500)
    k = _n(0.002)
    y[:k] *= _ramp(k)
    y[-_n(0.02):] *= _ramp(_n(0.02))[::-1]
    y /= np.max(np.abs(y)) + 1e-12
    _CACHE[key] = y
    return y


def _skor(kind="low", var=0):
    key = ("skor", kind, var)
    if key in _CACHE:
        return _CACHE[key]
    r = np.random.default_rng(zlib.crc32(repr(key).encode()))
    f0, f1, dec, nz = {"low": (150, 76, 0.30, 0.25), "slap": (240, 160, 0.10, 0.45),
                       "deep": (95, 52, 0.45, 0.15)}[kind]
    f0 *= r.uniform(0.97, 1.03)
    n = _n(dec * 5)
    t = _t(n)
    f = f1 + (f0 - f1) * np.exp(-t / 0.03)
    y = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / dec)
    y += nz * lp(r.standard_normal(n), 700 if kind != "slap" else 1500) * np.exp(-t / 0.015)
    y[:_n(0.001)] *= _ramp(_n(0.001))
    y /= np.max(np.abs(y))
    _CACHE[key] = y
    return y


def _ching(open_=True, var=0):
    key = ("ching", open_, var)
    if key in _CACHE:
        return _CACHE[key]
    r = np.random.default_rng(zlib.crc32(repr(key).encode()))
    fr = np.array([2890, 4170, 5310, 6880]) * r.uniform(0.99, 1.01, 4)
    dec = np.array([0.35, 0.25, 0.18, 0.12]) if open_ else np.full(4, 0.04)
    n = _n(dec.max() * 5)
    y = _modes(n, fr, dec, [1, 0.6, 0.4, 0.25])
    y += (0.1 if open_ else 0.5) * hp(r.standard_normal(n), 3000) * np.exp(-_t(n) / 0.01)
    y[:_n(0.001)] *= _ramp(_n(0.001))
    y /= np.max(np.abs(y))
    _CACHE[key] = y
    return y


def _lowhit(var=0):
    key = ("hit", var)
    if key in _CACHE:
        return _CACHE[key]
    r = np.random.default_rng(zlib.crc32(repr(key).encode()))
    n = _n(3.0)
    t = _t(n)
    f = 38 + 24 * np.exp(-t / 0.15)
    y = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / 0.9)
    y += 0.5 * lp(r.standard_normal(n), 250) * np.exp(-t / 0.25)
    y += 0.25 * np.sin(TAU * 2.0 * np.cumsum(f) / SR) * np.exp(-t / 0.5)
    y[:_n(0.006)] *= _ramp(_n(0.006))
    y /= np.max(np.abs(y))
    _CACHE[key] = y
    return y


# --- melody generation ------------------------------------------------------
_RHY = {
    "medium": [[1, 1, 1, 1], [1, .5, .5, 2], [.5, .5, 1, 1, 1], [1.5, .5, 1, 1], [2, 1, 1],
               [1, 1, 2], [.5, .5, .5, .5, 2]],
    "slow": [[2, 2], [3, 1], [1, 1, 2], [2, 1, 1], [1.5, .5, 2], [4]],
}
_END = {"medium": [[1, 1, 2], [2, 2], [4], [1, 3]], "slow": [[4], [2, 2], [1, 3]]}
_STEPS = np.array([-3, -2, -1, 0, 1, 2, 3])
_STEP_P = np.array([.04, .12, .30, .08, .30, .12, .04])


def _phrase(rng, style, bars, start, end, lo, hi, rest_p=0.06, rhythm=None):
    if rhythm is None:
        rhythm = []
        for b in range(bars):
            pool = _END[style] if b == bars - 1 else _RHY[style]
            rhythm.append(pool[rng.integers(len(pool))])
    durs = [x for bar in rhythm for x in bar]
    n = len(durs)
    degs, d = [], start
    for i in range(n):
        rem = n - 1 - i
        if i == 0:
            d = start
        elif rem == 0:
            d = end
        else:
            gap = end - d
            if abs(gap) > 2 * rem:
                d += int(np.sign(gap)) * 2
            else:
                d = int(np.clip(d + rng.choice(_STEPS, p=_STEP_P), lo, hi))
        degs.append(d)
    for i in range(1, n - 1):
        if rng.random() < rest_p:
            degs[i] = None
    return rhythm, durs, degs


def _melody(rng, cfg, nbars):
    """returns list of (beat_start, beats, degree_or_None, phrase_index)."""
    style = cfg["style"]
    T = 5
    lo, hi = 2, 10
    ev = []
    beat = 0.0
    ph = 0
    while beat < nbars * 4:
        open_end = T + int(rng.choice([-2, 3, -1]))  # e.g. G below / G above / A below
        rA, dA, gA = _phrase(rng, style, 4, T + int(rng.choice([0, 2, 3])), open_end, lo, hi)
        _, dA2, gA2 = _phrase(rng, style, 4, gA[0] if gA[0] is not None else T, T, lo, hi, rhythm=rA)
        half = sum(len(b) for b in rA[:2])
        gA2 = list(gA[:half]) + list(gA2[half:])
        rB, dB, gB = _phrase(rng, style, 4, T + int(rng.choice([2, 3, 4])), open_end, lo, hi)
        gA3 = list(gA2)
        j = int(rng.integers(1, max(2, len(gA3) - 1)))
        if gA3[j] is not None:
            gA3[j] = int(np.clip(gA3[j] + rng.choice([-1, 1]), lo, hi))
        for durs, degs in ((dA, gA), (dA2, gA2), (dB, gB), (dA2, gA3)):
            for du, dg in zip(durs, degs):
                ev.append((beat, du, dg, ph))
                beat += du
            ph += 1
    return ev


# --- stems --------------------------------------------------------------------
def _stem_roneat_notes(N, notes, muted=False, pan_fn=None):
    """notes: (time_s, midi, vel). returns stereo."""
    out = np.zeros((N, 2))
    for i, (ts, m, v) in enumerate(notes):
        y = _roneat_note(m, muted, var=i % 3) * v
        p = pan_fn(m) if pan_fn else 0.0
        _add(out, pan(y, p), _n(ts))
    return out


def _ron_pan(m):
    return float(np.clip((m - 66) / 30.0, -0.6, 0.6))


def _khloy(N, notes, rng, vib_rate=5.2, breath=0.10):
    """notes: (t0, dur, midi, vel). continuous legato bamboo-flute line (mono)."""
    if not notes:
        return np.zeros(N)
    target = np.full(N, np.nan)
    gate = np.zeros(N)
    onset = np.zeros(N, dtype=bool)
    for (t0, dur, m, v) in notes:
        i0 = _n(t0)
        if i0 >= N:
            continue
        gap = 0.04 if rng.random() < 0.3 else 0.0
        i1 = min(N, _n(t0 + max(0.05, dur - gap)))
        target[i0:i1] = m
        x = np.linspace(0, 1, max(i1 - i0, 1))
        gate[i0:i1] = v * (0.82 + 0.18 * np.sin(np.pi * x))
        onset[i0] = True
    valid = ~np.isnan(target)
    if not valid.any():
        return np.zeros(N)
    first = int(np.argmax(valid))
    idx = np.where(valid, np.arange(N), first)
    np.maximum.accumulate(idx, out=idx)
    target = target[idx]  # forward-fill pitch through rests
    mc = _smooth(target, 0.045)
    g = _smooth(_smooth(gate, 0.05), 0.03)
    last = np.where(onset, np.arange(N), 0)
    np.maximum.accumulate(last, out=last)
    tso = (np.arange(N) - last) / SR
    t = _t(N)
    depth = 0.16 * np.clip((tso - 0.22) / 0.45, 0, 1)
    vib = depth * np.sin(TAU * vib_rate * t + 0.6 * _srand(N, 0.3, rng, 0, TAU))
    f = _mtof(mc + vib)
    ph = TAU * np.cumsum(f) / SR
    tone = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.06 * np.sin(3 * ph)
    nz = rng.standard_normal(N)
    air = bp(nz, 500, 2200) * breath * (1 + 0.5 * np.sin(ph))
    chiff = hp(nz, 800) * 0.25 * np.exp(-tso / 0.03)
    y = (tone + air + chiff) * g
    return y


def _pad(N, segments, rng, att=1.2, rel=1.8, cutoff=1200.0):
    """segments: (t0, dur, [midis]). detuned saw pad, heavily low-passed. stereo."""
    L = np.zeros(N)
    R = np.zeros(N)
    for (t0, dur, midis) in segments:
        n = _n(dur + rel)
        env = np.ones(n)
        a = min(_n(att), n)
        env[:a] = _ramp(a)
        r = _n(rel)
        env[n - r:] *= _ramp(r)[::-1]
        i0 = _n(t0)
        for k, m in enumerate(midis):
            f = float(_mtof(m))
            amp = 1.0 / (1 + 0.5 * k)
            sl = _saw(f * 0.996, n, rng.random()) + 0.6 * _saw(f * 1.001, n, rng.random())
            sr_ = _saw(f * 1.004, n, rng.random()) + 0.6 * _saw(f * 0.999, n, rng.random())
            _add(L, sl * env * amp, i0)
            _add(R, sr_ * env * amp, i0)
    L = lp(lp(L, cutoff), cutoff)
    R = lp(lp(R, cutoff), cutoff)
    return np.stack([L, R], 1)


def _drone(N, freq, rng, swell_period=None):
    t = _t(N)
    y = np.sin(TAU * freq * t) + 0.45 * np.sin(TAU * 1.5 * freq * t + 1.0) \
        + 0.22 * np.sin(TAU * 2 * freq * t + 2.0)
    y += 0.3 * lp(lp(_saw(freq * 1.002, N), 260), 260)
    amp = 0.7 + 0.3 * _srand(N, 0.12, rng)
    if swell_period:
        ph = (t % swell_period) / swell_period
        amp *= 0.3 + 0.7 * np.sin(np.pi * ph) ** 2
    y *= amp
    L = y * (1 + 0.1 * np.sin(TAU * 0.07 * t))
    R = y * (1 - 0.1 * np.sin(TAU * 0.07 * t))
    return np.stack([L, R], 1) * 0.7


def _chord_voicing(r, scale, base):
    """open-fifth pentatonic voicing around base (midi)."""
    sc = set(scale)
    rr = base + (r % 12)
    if rr > base + 6:
        rr -= 12
    v = [rr, rr + 7, rr + 12]
    if (r + 4) % 12 in sc:
        v.append(rr + 16)
    elif (r + 3) % 12 in sc:
        v.append(rr + 15)
    elif (r + 2) % 12 in sc:
        v.append(rr + 14)
    return v


# --- cue definitions ----------------------------------------------------------
_CUES = {
    "opening": dict(bpm=84, root=72, scale="major", style="medium", prog=[0, 9, 2, 7, 0, 9, 7, 0],
                    plan=["roneat", "both", "khloy", "both"], pad_base=48, pad_lp=1100,
                    skor="light", ching="offbeat",
                    gains=dict(roneat=0.55, khloy=0.40, pad=0.10, skor=0.30, ching=0.05)),
    "tension_low": dict(bpm=60, root=57, scale="minor", style="slow", prog=[0, 0, 8, 8, 0, 0, 3, 7],
                        plan=[None], pad_base=45, pad_lp=550, sparse=(45, 0.28), drone=27.5 * 2,
                        skor="heart", ching=None,
                        gains=dict(sparse=0.75, pad=0.10, drone=0.10, skor=0.30)),
    "family_sad": dict(bpm=62, root=69, scale="minor", style="slow", prog=[0, 5, 8, 7, 0, 5, 10, 0],
                       plan=["khloy"], pad_base=45, pad_lp=1300, arp=(69, "quarter"),
                       skor=None, ching=None,
                       gains=dict(khloy=0.55, pad=0.16, arp=0.16)),
    "confront": dict(bpm=76, root=52, scale="minor", style="medium", prog=[0, 0, 0, 0, 0, 0, 10, 10],
                     plan=[None], pad_base=40, pad_lp=650, ostinato="confront", os_root=52,
                     drone=41.2, skor="pulse", ching="closed4",
                     gains=dict(ostinato=0.60, pad=0.08, drone=0.07, skor=0.30, ching=0.03)),
    "workers": dict(bpm=88, root=74, scale="minor", style="medium", prog=[0, 10, 5, 7, 0, 10, 7, 0],
                    plan=[None, None, "khloy", None], pad_base=50, pad_lp=900, ostinato="workers",
                    os_root=62, skor="workers", ching="offbeat",
                    gains=dict(ostinato=0.45, khloy=0.28, pad=0.09, skor=0.28, ching=0.045)),
    "police": dict(bpm=70, root=60, scale="minor", style="slow", prog=[0, 0, 8, 8, 0, 0, 10, 7],
                   plan=[None], pad_base=48, pad_lp=600, sparse=(48, 0.18), drone=65.4 / 1.0,
                   drone_swell=4, hits=True, skor="deep1", ching=None,
                   gains=dict(sparse=0.65, pad=0.10, drone=0.10, skor=0.25, hits=0.45)),
    "ending": dict(bpm=66, root=67, scale="major", style="slow", prog=[0, 9, 5, 7, 0, 9, 5, 0],
                   plan=["khloy", "khloy", "both", "khloy"], pad_base=43, pad_lp=1300,
                   arp=(67, "eighth"), skor="soft2", ching="bar",
                   gains=dict(khloy=0.50, roneat=0.35, pad=0.15, arp=0.20, skor=0.15, ching=0.035)),
}


def music(cue: str, duration: float, seed: int = 0) -> np.ndarray:
    """Cambodian-inspired underscore, any duration, 1.5 s fade in / 2.5 s fade out, -3 dBFS."""
    if cue not in _CUES:
        raise ValueError(f"unknown cue {cue!r}; choose from {MUSIC_CUES}")
    cfg = _CUES[cue]
    rng = _rng(seed, "music", cue)
    beat = 60.0 / cfg["bpm"]
    bar = 4 * beat
    N = _n(duration)
    NB = N + _n(4.0)
    nbars = int(np.ceil(duration / bar)) + 1
    scale = SCALES[cfg["scale"]]
    G = cfg["gains"]
    hum = lambda: rng.normal(0, 0.006)  # noqa: E731  humanize timing
    dry = np.zeros((NB, 2))
    send = np.zeros((NB, 2))

    def mix(st, gain, snd):
        nonlocal dry, send
        st = st * gain
        dry += st
        send += st * snd

    # ---- melody (roneat / khloy) ----
    plan = cfg["plan"]
    if any(p is not None for p in plan):
        ev = _melody(rng, cfg, nbars)
        ron_notes, khl_notes = [], []
        for (b0, nb, dg, ph) in ev:
            inst = plan[ph % len(plan)]
            if dg is None or inst is None or b0 >= nbars * 4:
                continue
            m = _dm(cfg["root"], scale, dg)
            t0 = b0 * beat
            if inst in ("khloy", "both"):
                khl_notes.append((t0, nb * beat, m, 0.8 + 0.2 * rng.random()))
            if inst in ("roneat", "both"):
                v0 = 0.75 + 0.2 * rng.random()
                if nb * beat >= 1.3 * beat and cfg["style"] == "medium" or nb >= 2:
                    step = float(np.clip(beat / 6, 0.09, 0.14))
                    k = int(nb * beat / step)
                    for j in range(k):
                        v = v0 * (1.0 if j == 0 else 0.5 * (1 - 0.4 * j / k) + 0.08 * rng.random())
                        ts = t0 + j * step + hum()
                        ron_notes.append((ts, m, v))
                        ron_notes.append((ts + 0.004, m - 12, v * 0.55))
                else:
                    ts = t0 + hum()
                    ron_notes.append((ts, m, v0))
                    ron_notes.append((ts + 0.004, m - 12, v0 * 0.55))
        if ron_notes and "roneat" in G:
            mix(_stem_roneat_notes(NB, ron_notes, pan_fn=_ron_pan), G["roneat"], 0.35)
        if khl_notes and "khloy" in G:
            k = _khloy(NB, khl_notes, rng)
            mix(pan(k, 0.18), G["khloy"], 0.4)

    # ---- harmony (pad + optional arpeggio) ----
    prog = cfg["prog"]
    segs = []
    b = 0
    while b < nbars:
        r = prog[b % len(prog)]
        L = 1
        while b + L < nbars and prog[(b + L) % len(prog)] == r and L < 4:
            L += 1
        segs.append((b * bar, L * bar, _chord_voicing(r, scale, cfg["pad_base"])))
        b += L
    mix(_pad(NB, segs, rng, cutoff=cfg["pad_lp"]), G["pad"] * 0.25, 0.3)

    if "arp" in cfg:
        aroot, kind = cfg["arp"]
        notes = []
        for bi in range(nbars):
            r = prog[bi % len(prog)]
            v = _chord_voicing(r, scale, aroot - 12)
            tones = [v[0], v[1], v[2], v[3] if len(v) > 3 else v[2] + 2, v[1] + 12, v[2] + 12]
            if kind == "eighth":
                pat, step = [0, 1, 2, 3, 4, 3, 2, 1], beat / 2
            else:
                pat, step = [0, 2, 3, 2], beat
            if bi % 2 == 1:
                pat = pat[::-1]
            for j, pi in enumerate(pat):
                vel = (0.7 if j == 0 else 0.45) * (0.9 + 0.2 * rng.random())
                notes.append((bi * bar + j * step + hum(), tones[pi], vel))
        mix(_stem_roneat_notes(NB, notes, pan_fn=lambda m: -_ron_pan(m)), G["arp"], 0.45)

    # ---- ostinato (muted roneat) ----
    if cfg.get("ostinato"):
        osr = cfg["os_root"]
        notes = []
        if cfg["ostinato"] == "confront":
            base = [5, 5, 8, 5, 5, 5, 9, 8, 5, 5, 8, 5, 5, 7, 6, 5]
            acc = [1, .55, .75, .55, .85, .55, .75, .6] * 2
            for bi in range(0, nbars, 2):
                for j, dg in enumerate(base):
                    ts = bi * bar + j * beat / 2 + hum()
                    notes.append((ts, _dm(osr, scale, dg), acc[j] * (0.9 + 0.15 * rng.random())))
        else:  # workers: restless, generated & slowly mutating
            pat = [5]
            for _ in range(15):
                pat.append(int(np.clip(pat[-1] + rng.choice([-2, -1, 0, 1, 2]), 3, 9)))
            sixteenth = rng.random(16) < 0.2
            for bi in range(0, nbars, 2):
                if bi % 8 == 0 and bi:
                    for _ in range(2):
                        j = int(rng.integers(1, 16))
                        pat[j] = int(np.clip(pat[j] + rng.choice([-1, 1]), 3, 9))
                for j, dg in enumerate(pat):
                    ts = bi * bar + j * beat / 2 + hum()
                    v = (0.9 if j % 4 == 0 else 0.6) * (0.85 + 0.2 * rng.random())
                    m = _dm(osr, scale, dg)
                    notes.append((ts, m, v))
                    if sixteenth[j]:
                        notes.append((ts + beat / 4, _dm(osr, scale, dg + 1), v * 0.6))
        mix(_stem_roneat_notes(NB, notes, muted=True, pan_fn=lambda m: -0.25), G["ostinato"], 0.25)

    # ---- sparse low roneat ----
    if cfg.get("sparse"):
        sroot, p = cfg["sparse"]
        notes = []
        nbeats = nbars * 4
        for bi in range(nbeats):
            if rng.random() < p:
                if rng.random() < 0.08:
                    m = sroot + 1  # soft b2 neighbor -> unease
                else:
                    m = _dm(sroot, scale, int(rng.choice([5, 5, 6, 7, 4, 3])))
                notes.append((bi * beat + hum(), m, 0.5 + 0.35 * rng.random()))
        mix(_stem_roneat_notes(NB, notes, pan_fn=lambda m: rng.uniform(-0.4, 0.4)), G["sparse"], 0.5)

    # ---- drone ----
    if cfg.get("drone"):
        sp = cfg.get("drone_swell")
        mix(_drone(NB, cfg["drone"], rng, sp * bar if sp else None), G["drone"], 0.2)

    # ---- percussion ----
    sk = cfg.get("skor")
    if sk:
        perc = np.zeros((NB, 2))
        pats = {
            "light": ([(0, "low", 0.9), (2.5, "slap", 0.4), (3, "low", 0.55)], 1),
            "pulse": ([(0, "low", 0.9), (1, "low", 0.55), (2, "low", 0.75), (3, "low", 0.55)], 1),
            "workers": ([(0, "low", 0.9), (1.5, "slap", 0.45), (2, "low", 0.6), (3.5, "slap", 0.4)], 1),
            "heart": ([(0, "deep", 0.8), (0.4, "deep", 0.5), (2, "deep", 0.6), (2.4, "deep", 0.35)], 1),
            "deep1": ([(0, "deep", 0.8)], 1),
            "soft2": ([(0, "low", 0.6), (3, "slap", 0.25)], 2),
        }
        pat, every = pats[sk]
        for bi in range(0, nbars, every):
            for (bt, kind, v) in pat:
                y = _skor(kind, int(rng.integers(3))) * v * (0.9 + 0.2 * rng.random())
                _add(perc, pan(y, -0.15), _n(bi * bar + bt * beat + hum()))
        mix(perc, G["skor"], 0.2)
    ch = cfg.get("ching")
    if ch:
        cst = np.zeros((NB, 2))
        for bi in range(nbars):
            if ch == "offbeat":
                hits = [(1, True), (3, True), (0, False), (2, False)]
            elif ch == "closed4":
                hits = [(3, False)]
            else:  # "bar"
                hits = [(0, True)] if bi % 2 == 0 else []
            for (bt, op) in hits:
                y = _ching(op, int(rng.integers(3))) * (1.0 if op else 0.5)
                _add(cst, pan(y, 0.35), _n(bi * bar + bt * beat + hum()))
        mix(cst, G["ching"], 0.35)
    if cfg.get("hits"):
        hst = np.zeros((NB, 2))
        for bi in range(0, nbars, 4):
            _add(hst, pan(_lowhit(bi // 4 % 3), 0.0), _n(bi * bar))
            if rng.random() < 0.4:
                _add(hst, pan(_lowhit(1) * 0.5, 0.0), _n((bi + 2) * bar + 2 * beat))
        mix(hst, G["hits"], 0.35)

    # ---- master: reverb, EQ, fades, normalize ----
    ir = _ir(2.2, 5500.0, 0.02, 7)
    wet = sps.oaconvolve(send, ir, axes=0)[:NB]
    y = (dry + 0.55 * wet)[:N]
    del dry, send, wet
    y = hp(y, 38)
    y = peaking(y, 2500, -4.5, 0.6)
    y = peaking(y, 1200, -1.5, 0.8)
    y = lp(y, 8000, 4)
    y = _fade(y, 1.5, 2.5)
    return _finish(y, peak=-3.0)


# ============================================================================
# AMBIENCE
# ============================================================================
def _clink(rng, f0=None, dec=None):
    f0 = f0 or rng.uniform(1200, 3000)
    dec = dec or rng.uniform(0.12, 0.4)
    ratios = np.array([1, 2.76, 5.40, 8.93]) * rng.uniform(0.98, 1.02, 4)
    n = _n(dec * 5)
    y = _modes(n, f0 * ratios, dec / np.array([1, 1.6, 2.6, 4]), [1, .5, .25, .12])
    k = _n(0.006)
    y[:k] += 0.4 * rng.standard_normal(k) * np.exp(-_t(k) / 0.001)
    y[:_n(0.0008)] *= _ramp(_n(0.0008))
    return y / (np.max(np.abs(y)) + 1e-12)


def _creak(dur, rng, rate0=40, rate1=80, modes=(380, 820, 1500, 2300), level=1.0):
    n = _n(dur)
    t = _t(n)
    rate = (rate0 + (rate1 - rate0) * t / dur) * (1 + 0.25 * (_srand(n, 14, rng) * 2 - 1))
    ph = np.cumsum(rate) / SR
    idx = np.nonzero(np.diff(np.floor(ph)) > 0)[0]
    env = np.sin(np.pi * t / dur) ** 0.7
    imp = np.zeros(n)
    imp[idx] = rng.uniform(0.5, 1.0, len(idx)) * env[idx]
    kn = _n(0.05)
    fr = np.array(modes) * rng.uniform(0.95, 1.05, len(modes))
    ker = _modes(kn, fr, [0.018, 0.012, 0.008, 0.005][:len(fr)], [1, .7, .45, .25][:len(fr)])
    y = sps.fftconvolve(imp, ker)[:n]
    return level * y / (np.max(np.abs(y)) + 1e-12)


def _wind(n, rng, lo=200, hi=900, rate=0.08, depth=0.7):
    w = bp(rng.standard_normal(n), lo, hi)
    sw = _srand(n, rate, rng)
    return w * (1 - depth + depth * sw ** 1.5)


def _chirp(dur, f_curve, rng, harm=0.08):
    n = _n(dur)
    x = np.linspace(0, 1, n)
    f = f_curve(x)
    ph = TAU * np.cumsum(f) / SR
    y = (np.sin(ph) + harm * np.sin(2 * ph)) * np.sin(np.pi * x) ** 2
    return y


def _bird_phrase(species, rng, song):
    parts = []
    if species == "sparrow":
        for _ in range(rng.integers(3, 7)):
            a, b, c = song
            parts.append(_chirp(rng.uniform(0.05, 0.08), lambda x: a + (b - a) * np.sin(np.pi * x) + (c - a) * x, rng))
            parts.append(np.zeros(_n(rng.uniform(0.06, 0.1))))
    elif species == "bulbul":
        for (f0, f1, d) in song:
            parts.append(_chirp(d, lambda x, f0=f0, f1=f1: f0 + (f1 - f0) * (0.5 - 0.5 * np.cos(np.pi * x)), rng, 0.15))
            parts.append(np.zeros(_n(0.03)))
    elif species == "trill":
        d = rng.uniform(0.5, 0.9)
        fc, fm = song
        parts.append(_chirp(d, lambda x: fc + 500 * np.sin(TAU * fm * x * d) - 300 * x, rng, 0.03))
    else:  # dove: coo-coo-crooo
        f = song
        for (d, g, rough) in ((0.25, 0.8, 0), (0.25, 0.8, 0), (0.55, 1.0, 1)):
            y = _chirp(d, lambda x: f * (1.05 - 0.12 * x), rng, 0.25)
            if rough:
                y *= 0.75 + 0.25 * np.sin(TAU * 28 * _t(len(y)))
            parts.append(y * g)
            parts.append(np.zeros(_n(0.12)))
    return np.concatenate(parts)


def _birds(n, rng):
    out = np.zeros((n, 2))
    birds = []
    for sp in ("sparrow", "bulbul", "sparrow", "trill", "dove", "bulbul"):
        if sp == "sparrow":
            song = (rng.uniform(3000, 3600), rng.uniform(4200, 5000), rng.uniform(3200, 3800))
            gap = (2, 7)
        elif sp == "bulbul":
            song = [(rng.uniform(1700, 2900), rng.uniform(1700, 3100), rng.uniform(0.1, 0.2))
                    for _ in range(rng.integers(3, 6))]
            gap = (4, 11)
        elif sp == "trill":
            song = (rng.uniform(4200, 5000), rng.uniform(20, 32))
            gap = (7, 16)
        else:
            song = rng.uniform(520, 640)
            gap = (8, 16)
        birds.append((sp, song, gap, rng.uniform(-0.85, 0.85), rng.uniform(0.3, 1.0)))
    for (sp, song, gap, p, g) in birds:
        t = rng.uniform(0, gap[1])
        while t < n / SR:
            y = _bird_phrase(sp, rng, song) * g * (0.7 + 0.3 * rng.random())
            _add(out, pan(y, p), _n(t))
            t += len(y) / SR + rng.uniform(*gap)
    out = lp(out, 4500 if True else 8000)
    return out


def _babble(n, rng, nvoices, f0range=(100, 230), rate=(3, 6), worried=0.0):
    out = np.zeros((n, 2))
    for _ in range(nvoices):
        f0 = rng.uniform(*f0range)
        intonation = 1 + (0.12 + 0.1 * worried) * (_srand(n, 2.5 + 2 * worried, rng) * 2 - 1)
        buzz = _saw(f0 * intonation, n, rng.random())
        buzz = lp(buzz, 3000)
        w = _srand(n, rng.uniform(*rate), rng)
        voiced = bp(buzz, 280, 900) * (1 - w) + 0.6 * bp(buzz, 900, 2000) * w
        syl = _srand(n, rng.uniform(*rate) * 1.3, rng) ** 2
        phrase = _smooth((_srand(n, 0.35, rng) > 0.35).astype(float), 0.08)
        env = syl * phrase
        unv = 0.04 * bp(rng.standard_normal(n), 2000, 5000) * env
        out += pan((voiced * env + unv) * rng.uniform(0.5, 1.0), rng.uniform(-0.8, 0.8))
    return out


def _horn(rng):
    d = 0.32
    parts = []
    f1, f2 = rng.uniform(330, 370), rng.uniform(410, 450)
    for dd in (d, d * 1.6):
        n = _n(dd)
        t = _t(n)
        y = np.tanh(2.5 * np.sin(TAU * f1 * t)) + 0.8 * np.tanh(2.5 * np.sin(TAU * f2 * t))
        y *= _env_ar(n, 0.02, 0.06)
        parts += [y, np.zeros(_n(0.12))]
    return lp(np.concatenate(parts), 1800)


def _engine_pass(rng, L):
    n = _n(L)
    x = np.linspace(-1, 1, n)
    f0 = rng.uniform(38, 55)
    f = f0 * (1 - 0.045 * np.tanh(x * 3))
    amp = np.exp(-(x / 0.42) ** 2)
    y = _saw(f, n) + 0.5 * _saw(2 * f * 1.003, n) + 0.6 * lp(rng.standard_normal(n), 300)
    y = lp(lp(y, 380), 380) * amp
    d = rng.choice([-1, 1])
    return pan(y, d * 0.7 * x)


def ambience(kind: str, duration: float, seed: int = 0) -> np.ndarray:
    """Background bed, 1 s fade in/out, about -12 dBFS RMS (office/home/night a bit quieter)."""
    if kind not in AMBIENCE_KINDS:
        raise ValueError(f"unknown ambience {kind!r}; choose from {AMBIENCE_KINDS}")
    rng = _rng(seed, "amb", kind)
    N = _n(duration)
    NB = N + _n(1.5)
    out = np.zeros((NB, 2))
    events = np.zeros((NB, 2))  # goes to reverb
    T = NB / SR

    if kind == "garage":
        rum = np.stack([lp(_brown(NB, rng), 180), lp(_brown(NB, rng), 180)], 1)
        out += rum * 0.22
        out += np.stack([_wind(NB, rng, 250, 900), _wind(NB, rng, 250, 900)], 1) * 0.12
        t = rng.uniform(2, 12)
        while t < T:
            L = rng.uniform(6, 10)
            _add(events, _engine_pass(rng, L) * rng.uniform(0.12, 0.22), _n(t))
            t += rng.uniform(15, 40)
        t = rng.exponential(2.5)
        while t < T:
            y = lp(_clink(rng), 6000) * rng.uniform(0.04, 0.12)
            _add(events, pan(y, rng.uniform(-0.9, 0.9)), _n(t))
            if rng.random() < 0.3:  # small double clink
                _add(events, pan(_clink(rng) * 0.04, rng.uniform(-0.9, 0.9)), _n(t + rng.uniform(0.1, 0.4)))
            t += rng.exponential(2.5)
        out += reverb(events, rt=1.3, wet=0.45, damp=4000, tail=False, seed=1)
        target = -12.0
    elif kind == "office":
        room = lp(np.stack([_brown(NB, rng), _brown(NB, rng)], 1), 350) * 0.3
        room += lp(rng.standard_normal((NB, 2)), 900) * 0.02
        out += room
        t = rng.exponential(3.5)
        while t < T:
            y = lp(lp(_clink(rng), 700), 700) * rng.uniform(0.15, 0.35)
            _add(events, pan(y, rng.uniform(-0.5, 0.5)), _n(t))
            t += rng.exponential(3.5)
        t = rng.uniform(5, 15)
        while t < T:
            y = _creak(rng.uniform(0.3, 0.8), rng, 25, 55, (300, 650, 1200)) * rng.uniform(0.06, 0.12)
            _add(events, pan(y, rng.uniform(-0.7, 0.7)), _n(t))
            t += rng.uniform(8, 25)
        t = rng.uniform(5, 25)
        while t < T:
            _add(events, lp(_engine_pass(rng, rng.uniform(6, 9)), 200) * 0.3, _n(t))
            t += rng.uniform(20, 45)
        out += reverb(events, rt=0.6, wet=0.3, damp=3000, tail=False, seed=2)
        target = -14.0
    elif kind == "home":
        w = np.stack([_wind(NB, rng, 300, 1400, 0.06), _wind(NB, rng, 300, 1400, 0.06)], 1)
        gust = _srand(NB, 0.1, rng)
        out += w * 0.35
        crackle = rng.standard_normal((NB, 2)) * (rng.random((NB, 2)) < 0.004)
        leaves = hp(bp(rng.standard_normal((NB, 2)), 2000, 6000) * 0.3 + bp(crackle, 1500, 5000), 1500)
        out += leaves * (0.02 + 0.1 * gust[:, None] ** 2)
        out += lp(np.stack([_brown(NB, rng), _brown(NB, rng)], 1), 120) * 0.1
        events += _birds(NB, rng) * 0.25
        out += reverb(events, rt=1.0, wet=0.35, damp=5000, tail=False, seed=3)
        target = -14.0
    elif kind == "street":
        w = np.stack([_wind(NB, rng, 250, 1200, 0.07), _wind(NB, rng, 250, 1200, 0.07)], 1)
        out += w * 0.35
        out += lp(np.stack([_brown(NB, rng), _brown(NB, rng)], 1), 200) * 0.15
        events += lp(_babble(NB, rng, 6, rate=(2.5, 5)), 1600) * 0.35
        dust = hp(rng.standard_normal((NB, 2)) * (rng.random((NB, 2)) < 0.002), 3000)
        out += dust * 0.05 * _srand(NB, 0.15, rng)[:, None]
        out += hp(rng.standard_normal((NB, 2)), 3000) * 0.01 * _srand(NB, 0.1, rng)[:, None] ** 3
        t = rng.uniform(4, 20)
        while t < T:
            _add(events, pan(_horn(rng) * rng.uniform(0.08, 0.16), rng.uniform(-0.8, 0.8)), _n(t))
            t += rng.uniform(18, 45)
        t = rng.uniform(3, 15)
        while t < T:
            _add(events, _engine_pass(rng, rng.uniform(5, 8)) * 0.18, _n(t))
            t += rng.uniform(15, 35)
        out += reverb(events, rt=1.2, wet=0.4, damp=4000, tail=False, seed=4)
        target = -12.0
    else:  # night
        t = _t(NB)
        cr = np.zeros((NB, 2))
        for i in range(int(rng.integers(3, 6))):
            fc = rng.uniform(4000, 5500)
            P = rng.uniform(0.3, 0.8)
            npul = int(rng.integers(3, 6))
            rate = rng.uniform(25, 35)
            dp = 0.6 / rate
            off = rng.uniform(0, P)
            phc = (t + off) % P
            inch = phc < npul / rate
            pp = (phc * rate) % 1.0
            gate = np.where(inch & (pp < dp * rate), np.sin(np.pi * pp / (dp * rate)) ** 2, 0.0)
            active = np.clip((_srand(NB, 0.08, rng) - 0.25) * 3, 0, 1)
            y = np.sin(TAU * fc * t + 0.2 * np.sin(TAU * 3 * fc * t)) * gate * active
            cr += pan(y * rng.uniform(0.3, 1.0), rng.uniform(-0.8, 0.8))
        fc = rng.uniform(6200, 6800)
        trill = np.sin(TAU * fc * t) * (0.5 + 0.5 * np.sin(TAU * 48 * t)) * _srand(NB, 0.05, rng) ** 2
        cr += pan(trill * 0.25, rng.uniform(-0.5, 0.5))
        events += lp(cr, 7500) * 0.2
        out += np.stack([_wind(NB, rng, 200, 700, 0.05), _wind(NB, rng, 200, 700, 0.05)], 1) * 0.25
        out += lp(np.stack([_brown(NB, rng), _brown(NB, rng)], 1), 100) * 0.08
        out += reverb(events, rt=1.4, wet=0.4, damp=6000, tail=False, seed=5)
        target = -14.0

    y = hp(out[:N], 40)
    y = _fade(y, 1.0, 1.0)
    return _finish(y, rms=target, max_peak=-1.0)


# ============================================================================
# SFX
# ============================================================================
def _thump(n, f0, f1, dec, rng, nz=0.3, nlp=800):
    t = _t(n)
    f = f1 + (f0 - f1) * np.exp(-t / 0.02)
    y = np.sin(TAU * np.cumsum(f) / SR) * np.exp(-t / dec)
    y += nz * lp(rng.standard_normal(n), nlp) * np.exp(-t / (dec * 0.4))
    y[:_n(0.001)] *= _ramp(_n(0.001))
    return y


def _burst(n, rng, lo, hi, dec, att=0.0005):
    y = bp(rng.standard_normal(n), lo, hi) * np.exp(-_t(n) / dec)
    k = max(1, _n(att))
    y[:k] *= _ramp(k)
    return y


def _tv_lp(x, w, lo, hi):
    return lp(x, lo) * (1 - w) + lp(x, hi) * w


def _engine(rpm, rng, cyl=4, rough=0.15):
    f = rpm / 60.0 * cyl / 2.0
    ph = np.cumsum(f) / SR
    k = np.floor(ph).astype(np.int64)
    frac = ph - k
    g = rng.uniform(1 - rough, 1 + rough, cyl)[k % cyl]
    jit = rng.uniform(1 - rough * 0.5, 1 + rough * 0.5, int(k.max()) + 2)[k]
    pulse = np.exp(-frac * 7.0) * g * jit
    body = lp(pulse, 700) + 0.4 * np.sin(TAU * np.cumsum(f / 2) / SR)
    noise = lp(rng.standard_normal(len(rpm)), 2500) * pulse * 0.25
    y = hp(body + noise, 25)
    return y / (np.max(np.abs(y)) + 1e-12)


def _sfx_raw(name, rng):
    """returns stereo raw signal + reverb settings."""
    if name.startswith("footsteps"):
        out = np.zeros((_n(2.6), 2))
        for s in range(4):
            t0 = 0.05 + s * rng.uniform(0.52, 0.6)
            p = -0.15 if s % 2 else 0.15
            if name == "footsteps_wood":
                n = _n(0.35)
                y = _thump(n, 130, 85, 0.05, rng, 0.4, 1500)
                y += 0.4 * _modes(n, np.array([220, 480, 910]) * rng.uniform(.97, 1.03), [.08, .05, .03], [1, .6, .3])
                toe = _thump(_n(0.2), 160, 110, 0.03, rng, 0.5, 2000) * 0.45
                _add(y, toe, _n(0.07))
                if s == 2:
                    _add(y, _creak(0.25, rng, 30, 50, (420, 900, 1600)) * 0.2, _n(0.02))
                rv = (0.7, 0.18, 4500)
            elif name == "footsteps_concrete":
                n = _n(0.3)
                y = _burst(n, rng, 600, 4000, 0.02) + 0.3 * _thump(n, 110, 80, 0.03, rng, 0.2)
                grit = rng.standard_normal(n) * (rng.random(n) < 0.01) * np.exp(-_t(n) / 0.05)
                y += bp(grit, 2000, 7000) * 0.8
                _add(y, _burst(_n(0.1), rng, 1000, 5000, 0.035, 0.005) * 0.5, _n(0.09))
                rv = (1.1, 0.22, 5000)
            else:  # sandal
                n = _n(0.4)
                y = 0.5 * _thump(n, 100, 70, 0.04, rng, 0.5, 1200)
                slap = hp(_burst(_n(0.06), rng, 800, 6000, 0.012), 700)
                _add(y, slap * 1.1, _n(rng.uniform(0.15, 0.2)))
                rv = (0.8, 0.18, 5000)
            _add(out, pan(y * rng.uniform(0.8, 1.0), p), _n(t0))
        return out, rv
    if name == "paper_page":
        n = _n(1.3)
        t = _t(n)
        nz = rng.standard_normal(n)
        lift = bp(nz, 1500, 6000) * np.clip(t / 0.4, 0, 1) ** 2 * (t < 0.45)
        crk = bp(nz * (rng.random(n) < 0.01), 1200, 5000) * 3 * (t < 0.5)
        sweep = np.clip((t - 0.35) / 0.55, 0, 1)
        sw = _tv_lp(bp(nz, 400, 5000), np.sin(np.pi * sweep), 900, 4000) * np.sin(np.pi * sweep) ** 2 * 1.4
        land = np.zeros(n)
        _add(land, _thump(_n(0.3), 90, 60, 0.04, rng, 1.0, 1500) * 0.6, _n(0.9))
        _add(land, _burst(_n(0.15), rng, 1000, 5000, 0.03) * 0.5, _n(0.9))
        y = (lift * 0.4 + crk * 0.3 + sw + land)
        return pan(y, 0) + pan(sw * 0.3, 0.4), (0.5, 0.15, 5000)
    if name == "pen_write":
        n = _n(1.5)
        t = _t(n)
        strokes = np.clip((_srand(n, 7, rng) - 0.3) * 3, 0, 1) * _env_ar(n, 0.05, 0.1)
        fric = 1 + 0.6 * (_srand(n, 150, rng) * 2 - 1)
        y = bp(rng.standard_normal(n), 1800, 5000) * strokes * fric
        y += 0.3 * lp(rng.standard_normal(n), 400) * strokes
        return pan(y, 0.1), (0.4, 0.12, 6000)
    if name == "chair_wood":
        n = _n(1.5)
        y = np.zeros(n)
        _add(y, _creak(0.6, rng, 45, 90, (380, 820, 1500, 2300)), _n(0.05))
        scr = bp(rng.standard_normal(_n(0.7)), 300, 2000) * np.sin(np.pi * np.linspace(0, 1, _n(0.7))) \
            * (0.6 + 0.4 * _srand(_n(0.7), 20, rng))
        _add(y, scr * 0.35, _n(0.5))
        _add(y, _thump(_n(0.3), 140, 90, 0.05, rng, 0.5, 1500) * 0.7, _n(1.2))
        return pan(y, -0.1), (0.6, 0.2, 5000)
    if name == "desk_knock":
        n = _n(0.9)
        y = np.zeros(n)
        for i in range(3):
            k = _modes(_n(0.25), np.array([180, 410, 760, 1250]) * rng.uniform(.98, 1.02), [.08, .06, .04, .03], [1, .7, .45, .3])
            k[:_n(0.004)] += lp(rng.standard_normal(_n(0.004)), 4000) * 0.6
            k[:_n(0.0005)] *= _ramp(_n(0.0005))
            _add(y, k * (1.0 if i == 0 else 0.85), _n(0.02 + i * 0.19))
        return pan(y, 0), (0.6, 0.2, 5000)
    if name in ("car_arrive", "car_depart", "jeep_arrive"):
        if name == "car_arrive":
            T = 5.2
            n = _n(T)
            t = _t(n)
            rpm = np.interp(t, [0, 2.8, 3.0, 4.3, 4.8, 5.2], [1500, 850, 750, 740, 100, 0])
            rpm *= 1 + 0.02 * np.sin(TAU * 1.3 * t)
            dist = np.interp(t, [0, 2.8, 5.2], [0.18, 1.0, 1.0])
            amp = np.interp(t, [0, 4.3, 4.8, 5.0], [1, 1, 0.3, 0])
            eng = _engine(rpm, rng, 4, 0.12)
            eng = _tv_lp(eng, dist, 500, 2200) * dist * amp
            road = lp(_brown(n, rng), 400) * np.clip(1 - t / 2.9, 0, 1) * dist * 0.3
            y = eng + road
            _add(y, _thump(_n(0.4), 70, 45, 0.08, rng, 0.3, 500) * 0.4, _n(4.85))
            return pan(y, np.interp(t, [0, 2.8, 5.2], [-0.8, -0.05, 0])), (0.9, 0.12, 4000)
        if name == "car_depart":
            T = 5.5
            n = _n(T)
            t = _t(n)
            st = np.zeros(n)
            ns = _n(1.0)
            ts = _t(ns)
            crank = (np.sin(TAU * 140 * ts) + 0.5 * np.sin(TAU * 280 * ts) + 0.4 * lp(rng.standard_normal(ns), 1500))
            crank *= (0.5 + 0.5 * np.sin(TAU * 5.5 * ts) ** 2) * _env_ar(ns, 0.03, 0.08)
            st[:ns] = lp(crank, 2000) * 0.35
            rpm = np.interp(t, [0, 1.0, 1.3, 2.0, 2.3, 3.8, 4.0, 5.5], [180, 200, 1300, 800, 900, 1900, 1300, 1800])
            amp = np.interp(t, [0, 0.9, 1.05, 2.3, 5.5], [0.25, 0.3, 1, 1, 0.08])
            dist = np.interp(t, [0, 2.3, 5.5], [1, 1, 0.0])
            eng = _engine(rpm, rng, 4, 0.12)
            eng = _tv_lp(eng, dist, 450, 2200) * amp
            y = eng + st
            _add(y, _thump(_n(0.25), 90, 60, 0.05, rng, 0.4, 1200) * 0.3, _n(2.2))
            y = _fade(y, 0.0, 0.5)
            return pan(y, np.interp(t, [0, 2.3, 5.5], [0, 0, 0.8])), (0.9, 0.12, 4000)
        # jeep
        T = 4.2
        n = _n(T)
        t = _t(n)
        rpm = np.interp(t, [0, 1.2, 1.35, 2.8, 3.1, 4.2], [2000, 1700, 2100, 1100, 900, 880])
        rpm *= 1 + 0.03 * (_srand(n, 6, rng) * 2 - 1)
        dist = np.interp(t, [0, 3.0, 4.2], [0.2, 1, 1])
        eng = _engine(rpm, rng, 4, 0.3)
        eng = _tv_lp(eng, dist, 500, 2500) * dist
        grav = bp(rng.standard_normal(n) * (rng.random(n) < 0.02), 1500, 6000) * np.clip(1 - t / 3.1, 0, 1) * dist * 0.8
        rattle = np.zeros(n)
        for _ in range(12):
            _add(rattle, _clink(rng, rng.uniform(1500, 2500), 0.03) * 0.08 * dist[min(n - 1, _n(1))], _n(rng.uniform(0, 4)))
        y = eng + grav + rattle
        _add(y, bp(rng.standard_normal(_n(0.4)), 300, 1500) * np.exp(-_t(_n(0.4)) / 0.15) * 0.25, _n(2.9))
        y = _fade(y, 0.0, 0.4)
        return pan(y, np.interp(t, [0, 3, 4.2], [0.8, 0.05, 0])), (0.9, 0.12, 4000)
    if name == "car_door":
        n = _n(0.9)
        y = _thump(n, 90, 62, 0.16, rng, 0.8, 1200) + 0.5 * _thump(n, 140, 110, 0.08, rng, 0, 1000)
        latch = _modes(_n(0.1), np.array([2100, 3300, 4900]) * rng.uniform(.98, 1.02), [.03, .02, .015], [1, .6, .4])
        _add(y, latch * 0.3, _n(0.012))
        _add(y, _modes(_n(0.3), [420, 690], [0.12, 0.08], [0.2, 0.15]), _n(0.005))
        return pan(y, 0.1), (0.8, 0.18, 4000)
    if name == "tool_clank":
        n = _n(1.6)
        y = np.zeros(n)
        f0 = rng.uniform(1300, 1600)
        for i, (tt, a) in enumerate([(0, 1), (0.18, 0.55), (0.31, 0.35), (0.40, 0.22), (0.46, 0.12)]):
            ring = _modes(_n(0.9), f0 * np.array([1, 2.31, 4.12, 6.2]) * rng.uniform(.99, 1.01, 4),
                          np.array([.35, .22, .14, .08]) * (0.5 + 0.5 * a), [1, .6, .35, .2])
            ring[:_n(0.01)] += _burst(_n(0.01), rng, 1000, 5000, 0.003) * 1.5
            ring[:_n(0.0005)] *= _ramp(_n(0.0005))
            _add(y, ring * a, _n(tt + rng.uniform(-0.01, 0.01)))
        _add(y, bp(rng.standard_normal(_n(0.3)), 1500, 5000) * _env_ar(_n(0.3), 0.05, 0.2) * 0.08, _n(0.5))
        return pan(y, rng.uniform(-0.3, 0.3)), (1.1, 0.22, 5000)
    if name == "hammer_metal":
        n = _n(2.3)
        y = np.zeros(n)
        for i in range(3):
            fr = np.array([520, 1340, 2410, 3790, 5100]) * rng.uniform(.995, 1.005, 5)
            ring = _modes(_n(1.2), fr, [0.9, 0.6, 0.4, 0.25, 0.15], [1, .7, .45, .3, .15])
            ring += _thump(_n(1.2), 160, 120, 0.03, rng, 0.8, 3000) * 0.8
            ring[:_n(0.0005)] *= _ramp(_n(0.0005))
            _add(y, ring * (1 if i < 2 else 1.1), _n(0.02 + i * 0.55))
        return pan(lp(y, 7000), 0.2), (1.1, 0.2, 5000)
    if name == "coins":
        n = _n(1.3)
        y = np.zeros((n, 2))
        times = np.sort(rng.uniform(0, 0.7, int(rng.integers(6, 10))))
        for tt in times:
            f0 = rng.uniform(3000, 5000)
            c = _modes(_n(0.5), f0 * np.array([1, 1.53, 2.12, 2.7]), np.array([.2, .12, .08, .05]) * rng.uniform(.4, 1),
                       [1, .7, .5, .3])
            c[:_n(0.0005)] *= _ramp(_n(0.0005))
            _add(y, pan(c * rng.uniform(0.4, 1.0), rng.uniform(-0.4, 0.4)), _n(tt))
        return lp(y, 9000), (0.5, 0.15, 7000)
    if name == "banknotes":
        n = _n(1.6)
        y = np.zeros(n)
        tt = 0.03
        while tt < 1.45:
            fl = _burst(_n(0.12), rng, 1200, 5000, 0.035, 0.005)
            fl[:_n(0.003)] += bp(rng.standard_normal(_n(0.003)), 2000, 5000) * 0.8
            _add(y, fl * rng.uniform(0.6, 1.0), _n(tt))
            tt += rng.uniform(0.12, 0.18)
        y += bp(rng.standard_normal(n), 800, 4000) * 0.05 * _env_ar(n, 0.1, 0.2)
        return pan(y, -0.1), (0.4, 0.12, 6000)
    if name == "police_whistle":
        n = _n(1.3)
        t = _t(n)
        pea = 0.5 + 0.5 * np.sin(TAU * 32 * t + 0.5 * _srand(n, 5, rng))
        f = 2250 * (1 + 0.03 * np.clip(t / 0.08, 0, 1)) * (1 + 0.012 * pea)
        ph = TAU * np.cumsum(f) / SR
        y = (np.sin(ph) + 0.08 * np.sin(2 * ph)) * (0.75 + 0.25 * pea)
        y += 0.15 * bp(rng.standard_normal(n), 1500, 4000)
        y *= _env_ar(n, 0.04, 0.2)
        y = lp(y, 4500)
        return pan(y, 0.2), (1.0, 0.25, 4500)
    if name == "crowd_murmur":
        n = _n(5.0)
        y = _babble(n, rng, 14, (110, 250), rate=(3.5, 6.5), worried=0.6)
        y = lp(y, 2500) * (0.7 + 0.3 * _srand(n, 0.4, rng))[:, None]
        return _fade(y, 0.6, 0.8), (1.0, 0.35, 3500)
    if name == "gasp_room":
        n = _n(2.2)
        t = _t(n)
        rise = lp(rng.standard_normal(n), 220) * np.clip(t / 0.6, 0, 1) ** 3 * (t < 0.62)
        y = rise * 0.8
        hit = _lowhit(0)[: n - _n(0.6)] * 0.9
        _add(y, hit, _n(0.6))
        sh = (np.sin(TAU * 110 * t) + 0.6 * np.sin(TAU * 164.8 * t)) * np.clip((t - 0.6) / 0.05, 0, 1) * np.exp(-np.clip(t - 0.6, 0, None) / 0.7) * 0.12
        y += sh
        y = _fade(y, 0.0, 0.3)
        return pan(y, 0), (2.4, 0.4, 3000)
    if name == "door_wood":
        n = _n(3.0)
        y = np.zeros(n)
        latch = _modes(_n(0.08), [1800, 2900, 4300], [.02, .015, .01], [1, .6, .3])
        _add(y, latch * 0.4, _n(0.02))
        _add(y, _creak(1.1, rng, 20, 45, (300, 700, 1300, 2100)) * 0.55, _n(0.12))
        _add(y, _creak(0.45, rng, 50, 30, (300, 700, 1300, 2100)) * 0.35, _n(1.85))
        cl = _thump(_n(0.6), 100, 70, 0.1, rng, 0.6, 1200) + 0.5 * _modes(_n(0.6), [210, 470, 880], [.1, .06, .04], [1, .6, .3])
        _add(y, cl, _n(2.35))
        _add(y, latch * 0.35, _n(2.37))
        return pan(y, -0.2), (0.7, 0.22, 4500)
    if name == "whoosh_soft":
        n = _n(1.0)
        t = _t(n)
        x = t / t[-1]
        center = np.exp(np.log(300) + (np.log(1500) - np.log(300)) * np.sin(np.pi * np.clip(x * 1.1, 0, 1)))
        nz = rng.standard_normal(n)
        bands = [250, 400, 630, 1000, 1600, 2500]
        y = np.zeros(n)
        for fc in bands:
            w = np.exp(-((np.log(center) - np.log(fc)) / 0.4) ** 2)
            y += bp(nz, fc / 1.4, fc * 1.4) * w
        y *= np.sin(np.pi * x) ** 2 * np.exp(-((x - 0.55) / 0.35) ** 2)
        return pan(lp(y, 5000), -0.6 + 1.2 * x), (0.6, 0.2, 5000)
    if name == "heartbeat_soft":
        n = _n(2.9)
        y = np.zeros(n)
        for i in range(3):
            t0 = 0.05 + i * 0.91
            _add(y, _thump(_n(0.4), 70, 45, 0.09, rng, 0.1, 200), _n(t0))
            _add(y, _thump(_n(0.4), 75, 55, 0.07, rng, 0.1, 200) * 0.7, _n(t0 + 0.28))
        return pan(lp(y, 220), 0), (0.5, 0.1, 2000)
    raise ValueError(f"unknown sfx {name!r}; choose from {SFX_NAMES}")


def sfx(name: str, seed: int = 0) -> np.ndarray:
    """One-shot sound effect at natural length, -6 dBFS peak."""
    rng = _rng(seed, "sfx", name)
    y, (rt, wet, damp) = _sfx_raw(name, rng)
    y = reverb(y, rt=rt, wet=wet, damp=damp, predelay=0.01, tail=True, seed=11)
    y = lp(hp(y, 30), 11000)
    y = _trim_tail(y, -60.0)
    return _finish(y, peak=-6.0)


# ============================================================================
# demo / self test
# ============================================================================
def _write(path, x):
    import soundfile as sf
    sf.write(path, x, SR, subtype="PCM_16")


def _report(tag, x, dt):
    bad = (not np.all(np.isfinite(x))) or np.max(np.abs(x)) >= 1.0
    dc = float(np.max(np.abs(x.mean(axis=0))))
    print(f"{tag:28s} dur={len(x)/SR:7.2f}s peak={peak_db(x):6.2f} dB rms={loudness_rms_db(x):7.2f} dB "
          f"dc={dc:.1e} t={dt:5.2f}s {'BAD' if bad else 'ok'}")
    return not bad


if __name__ == "__main__":
    outdir = sys.argv[1] if len(sys.argv) > 1 else "audio_tests"
    dur = float(sys.argv[2]) if len(sys.argv) > 2 else 20.0
    os.makedirs(outdir, exist_ok=True)
    ok = True
    for c in MUSIC_CUES:
        t0 = time.time()
        x = music(c, dur, seed=1)
        ok &= _report(f"music:{c}", x, time.time() - t0)
        _write(os.path.join(outdir, f"music_{c}.wav"), x)
    for k in AMBIENCE_KINDS:
        t0 = time.time()
        x = ambience(k, dur, seed=1)
        ok &= _report(f"ambience:{k}", x, time.time() - t0)
        _write(os.path.join(outdir, f"amb_{k}.wav"), x)
    for s in SFX_NAMES:
        t0 = time.time()
        x = sfx(s, seed=1)
        ok &= _report(f"sfx:{s}", x, time.time() - t0)
        _write(os.path.join(outdir, f"sfx_{s}.wav"), x)
    t0 = time.time()
    x = music("opening", 150.0, seed=2)
    ok &= _report("music:opening 150s", x, time.time() - t0)
    x = fit(sfx("coins"), 3.0)
    assert x.shape == (_n(3.0), 2)
    print("ALL OK" if ok else "PROBLEMS FOUND")
