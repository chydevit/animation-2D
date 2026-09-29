# Frame renderer: draws any global time t of the film, and encodes shots to MP4 via ffmpeg.
#   ~/anim-env/bin/python render.py still <t> out.png
#   ~/anim-env/bin/python render.py shotstill <i> [u] out.png
#   ~/anim-env/bin/python render.py shots [ids...]        (renders visuals/shots/*.mp4 in parallel)
import os, sys, math, json, random, subprocess, time
import numpy as np
import skia
import soundfile as sf
from gfx import Ctx, rgb, mix, lerp, ease, rad_grad, lin_grad, poly, rrect, smooth, shade, light, OUTLINE
from chars import Rig, CAST, POSES, EXPR, STAND, blend_pose, SEATED, expr_for
import config
import sets as S
from plan import build, FINAL, FPS, FADE
from script_data import voice_of
try:                      # optional story-specific cut-aways (story/story_art.py: INSERTS = {name: fn(R, c, t, shot, u)})
    import story_art as STORY_ART
except ImportError:
    STORY_ART = None

W, H = 1920, 1080
SHOTS_DIR = os.path.join(FINAL, "visuals", "shots")
FRAMES_DIR = os.path.join(FINAL, "visuals", "storyboard")
DLG = os.path.join(FINAL, "audio", "dialogue")
CARDS = os.path.join(FINAL, "characters", "cards")

_TL = None
def TL():
    global _TL
    if _TL is None:
        _TL = build()
    return _TL

RIGS = {k: Rig(k) for k in CAST}
_IMG = {}
def card(name):
    p = os.path.join(CARDS, name + ".png")
    if name not in _IMG:
        _IMG[name] = skia.Image.open(p) if os.path.exists(p) else None
    return _IMG[name]

# ───────────────────────────────────────────────────────────── lip-sync analysis
_LS = {}
def lipsync(file):
    if file in _LS:
        return _LS[file]
    y, sr = sf.read(os.path.join(DLG, file))
    if y.ndim > 1:
        y = y.mean(1)
    hop = sr // FPS
    n = len(y) // hop + 1
    env, cen = np.zeros(n), np.zeros(n)
    win = np.hanning(hop * 2)
    freqs = np.fft.rfftfreq(hop * 2, 1 / sr)
    for i in range(n):
        seg = y[max(0, i * hop - hop // 2): i * hop + hop + hop // 2]
        if len(seg) < hop * 2:
            seg = np.pad(seg, (0, hop * 2 - len(seg)))
        seg = seg[:hop * 2]
        env[i] = np.sqrt(np.mean(seg ** 2))
        sp = np.abs(np.fft.rfft(seg * win))
        cen[i] = (sp * freqs).sum() / (sp.sum() + 1e-9)
    ref = np.percentile(env, 92) + 1e-6
    env = np.clip(env / ref, 0, 1.3)
    shapes = []
    hold, last = 0, "closed"
    for i in range(n):
        e, c = env[i], cen[i]
        if e < 0.12:
            sh = "closed"
        elif e < 0.35:
            sh = "small" if c > 1200 else "U"
        elif c > 2600:
            sh = "E" if e < 0.7 else "wide"
        elif c > 1700:
            sh = "A" if e > 0.62 else "I"
        elif c > 1100:
            sh = "A" if e > 0.8 else "O"
        else:
            sh = "O" if e > 0.5 else "U"
        if sh != last and hold < 2:
            sh = last; hold += 1
        else:
            hold = 0 if sh != last else hold + 1
            last = sh
        shapes.append(sh)
    _LS[file] = (env, shapes)
    return _LS[file]

def mouth_for(name, t, shot):
    """mouth (shape, amount) when `name` is the speaker of `shot` and speaking aloud at t."""
    if shot.get("speaker") != name or not shot.get("audio") or not shot.get("speech"):
        return (None, 0.0)
    if "inner voice" in shot.get("act", ""):
        return (None, 0.0)
    s0, s1 = shot["speech"]
    if s0 <= t <= s1 + 0.1:
        env, shapes = lipsync(shot["audio"])
        i = int((t - s0) * FPS)
        if 0 <= i < len(env):
            return (shapes[i], float(min(1.0, env[i] * 1.1)))
    return (None, 0.0)

# ───────────────────────────────────────────────────────────── character state at time t
def blink_amt(name, t):
    rng = random.Random(sum(map(ord, name)))
    period = rng.uniform(2.8, 4.6)
    ph = (t + rng.uniform(0, period)) % period
    if ph < 0.13:
        return math.sin(ph / 0.13 * math.pi)
    return 0.0

def idle(name, st, t, walking=False):
    ph = (sum(map(ord, name)) % 100) / 16.0
    st["pose"] = dict(st["pose"])
    if not walking:
        st["pose"]["head"] = st["pose"].get("head", 0) + 1.3 * math.sin(t * 0.83 + ph) + 0.6 * math.sin(t * 2.1 + ph * 2)
        st["pose"]["torso"] = st["pose"].get("torso", 0) + 0.5 * math.sin(t * 0.47 + ph)
        dart = math.sin(t * 0.37 + ph * 3)
        st["look"] = (st["look"][0] + (0.12 if dart > 0.85 else 0.0), st["look"][1])
    m = st.get("mouth", (None, 0))
    if m[1] > 0.05:
        st["pose"]["head"] = st["pose"].get("head", 0) + 2.2 * math.sin(t * 7.1) * m[1]
    return st

def acting(name, st, t, shot, stage=None):
    """speech-driven acting: nods on stressed syllables, brow lifts, a small lean toward the listener;
    listeners nod now and then while someone else talks."""
    sp = shot.get("speaker")
    p = st["pose"]
    ex = st["expr"]
    if sp == name and shot.get("audio") and shot.get("speech") and "inner voice" not in shot.get("act", ""):
        s0, s1 = shot["speech"]
        if s0 <= t <= s1:
            env, _ = lipsync(shot["audio"])
            i = int((t - s0) * FPS)
            e = float(env[min(i, len(env) - 1)])
            onset = max(0.0, e - float(env[max(0, i - 4)]))            # a syllable/stress onset
            p["head"] = p.get("head", 0) + 5.5 * min(1.0, onset * 1.6)  # nod down on the stress
            ex["bh"] = ex.get("bh", 0) + 0.05 * min(1.0, e)             # brows lift with loudness
            u = (t - s0) / max(0.3, s1 - s0)
            if not p.get("lie") and not p.get("seat"):
                p["torso"] = p.get("torso", 0) + 2.5 * math.sin(math.pi * min(1, u))   # lean in while talking
    elif sp and sp != "narrator" and sp != name and shot.get("speech"):
        s0, s1 = shot["speech"]
        if s0 <= t <= s1 + 0.4:
            ph = (sum(map(ord, name)) % 7) * 0.9
            k = max(0.0, math.sin((t - s0) * 1.4 + ph)) ** 8           # an occasional slow nod
            p["head"] = p.get("head", 0) + 4.0 * k
    return st

def simple_state(name, t, pose="stand", facing=1, expr="neutral", shot=None, look=(0.45, 0.0), walk=False,
                 scale=1.0, speed=1.7, extra=None):
    p = dict(POSES.get(pose, POSES["stand"]))
    if extra:
        p.update(extra)
    mouth = mouth_for(name, t, shot) if shot else (None, 0.0)
    ex = expr
    if shot and shot.get("speaker") == name:
        ex = shot.get("expr", expr)
    st = dict(pose=p, facing=facing, t=t, blink=blink_amt(name, t), expr=dict(EXPR.get(ex, EXPR["neutral"])),
              mouth=mouth, look=look, walk=(t * 2 * math.pi * speed) if walk else None,
              breath=math.sin(t * 2 * math.pi * 0.23), scale=scale)
    st = idle(name, st, t, walk)
    return acting(name, st, t, shot) if shot else st

def char_state(name, t, shot, stage, mood, start_facing):
    x, d, walking = stage.at(name, t)
    base, prev, since = stage.base_at(name, t)
    if base == "walk" and not walking:
        base = "stand"
    bp = POSES.get(base, POSES["stand"])
    pp = POSES.get(prev if prev != "walk" else "stand", POSES["stand"])
    pose = blend_pose(pp, bp, since / 0.6) if since < 0.6 else dict(bp)
    g, g_in, g_left = stage.gesture(name, t)
    riding = base == "cyclo"
    if g and g in POSES and not (walking and not riding):
        gp = dict(POSES[g])
        if riding:
            gp = dict(pose, **{k: v for k, v in gp.items() if k not in ("seat", "cyclo", "nhip", "nkn", "fhip", "fkn")})
        elif (pose.get("seat", 0) or 0) > 0.5 or (pose.get("kneel", 0) or 0) > 0.5:
            for k in ("seat", "floor", "kneel", "nhip", "nkn", "fhip", "fkn"):
                gp[k] = pose.get(k, 0)
            gp["torso"] = pose["torso"] * 0.5 + gp.get("torso", 0) * 0.5
        w_in = ease(g_in / 0.35)
        w_out = ease((g_left + 0.5) / 0.5) if g_left < 0 else 1.0
        pose = blend_pose(pose, gp, min(w_in, w_out))
    walk = t * 2 * math.pi * 1.7 if walking else None
    speaker = shot.get("speaker")
    facing = start_facing.get(name, 1)
    md = stage.move_dir(name, t)
    if walking and md is not None:
        facing = md
    elif base in ("work", "hoe", "sweep", "stir", "bed", "cyclo", "write", "desk", "sit_work") or pose.get("lie"):
        facing = start_facing.get(name, 1) if md is None else facing
        if base == "cyclo":
            facing = start_facing.get(name, 1)
            for (t0, t1, a, b) in stage.moves.get(name, []):
                if t1 <= t and t1 > t0:
                    facing = 1 if b[0] >= a[0] else -1
    else:
        target = None
        if speaker == name:
            target = shot.get("to")
        elif speaker and speaker not in ("narrator",) and speaker in shot["cast"]:
            target = speaker
        tx = None
        if target and target != name and stage.vis(target, t) and abs(stage.at(target, t)[0]) < 900:
            tx = stage.at(target, t)[0]
        else:
            best = None
            for o in shot["cast"]:
                if o != name and stage.vis(o, t):
                    ox = stage.at(o, t)[0]
                    if abs(ox) > 900:
                        continue
                    dd = abs(ox - x)
                    if best is None or dd < best[0]:
                        best = (dd, ox)
            tx = best[1] if best else None
        if tx is not None and abs(tx - x) > 1:
            facing = 1 if tx >= x else -1
    ex_name = mood.get(name, "neutral")
    mouth = mouth_for(name, t, shot)
    if speaker == name:
        ex_name = shot.get("expr", "neutral")
    ex = dict(EXPR.get(ex_name, EXPR["neutral"]))
    look_y = 0.25 if base in ("write", "desk") else (0.1 if base in SEATED else 0.0)
    if g in ("head_down",) or base in ("head_down", "kneel_grief"):
        look_y = 0.5
    st = dict(pose=pose, facing=facing, t=t, blink=blink_amt(name, t), expr=ex, mouth=mouth,
              look=(0.45, look_y), walk=walk, breath=math.sin(t * 2 * math.pi * 0.23 + sum(map(ord, name)) % 7),
              scale=S.depth_scale(d), shadow=not pose.get("lie"), base=base, moving=walking)
    st = idle(name, st, t, walking and not riding)
    return x, d, acting(name, st, t, shot)

def head_world(name, x, d, st):
    rig = RIGS[name]
    J = rig.skeleton(st["pose"], st["t"], st.get("breath", 0), st.get("walk"))
    sc = st["scale"]
    hx, hy = J["head"]
    if st["pose"].get("lie"):
        if st["pose"].get("bed"):
            a = math.radians(-82)
            dy = -64
        else:
            a = math.radians(-90); dy = -12
        rx, ry = hx * math.cos(a) - (hy + 0) * math.sin(a), hx * math.sin(a) + hy * math.cos(a)
        return x + rx * sc * st["facing"], S.depth_y(d) + (ry + dy) * sc, rig.s["head_r"] * sc
    return x + hx * sc * st["facing"], S.depth_y(d) + hy * sc, rig.s["head_r"] * sc

# ───────────────────────────────────────────────────────────── camera
def frame_for(cam, states):
    """-> (cx, cy, zoom) in world coordinates."""
    def hw(n):
        if n in states:
            x, d, st = states[n][:3]
            return head_world(n, x, d, st)
        return (0, -150, 14)
    kind, _, arg = (cam or "wide").partition(":")
    if kind == "wide":
        xs = [states[n][0] for n in states if states[n][3] and abs(states[n][0]) < 820]
        if xs:
            lo, hi = min(xs) - 170, max(xs) + 170
            span = min(max(hi - lo, 880), 1500)
            cx = (lo + hi) / 2
        else:
            span, cx = 1200, 0
        zoom = W / span
        cy = -150 - span * 0.09
        return cx, cy, zoom
    if kind == "two":
        a, b = arg.split(",")
        ha, hb = hw(a), hw(b)
        lo, hi = min(ha[0], hb[0]) - 100, max(ha[0], hb[0]) + 100
        top = min(ha[1], hb[1]) - 48
        bot = max(ha[1], hb[1]) + 120
        zoom = min(W / (hi - lo), H / (bot - top))
        return (lo + hi) / 2, (top + bot) / 2 + 5, zoom
    if kind in ("med", "mcu", "cu"):
        n = arg
        hx, hy, hr = hw(n)
        facing = states[n][2]["facing"] if n in states else 1
        span_h = {"med": 150, "mcu": 92, "cu": 58}[kind] * hr / 14.5
        zoom = H / span_h
        off_y = {"med": 0.26, "mcu": 0.16, "cu": 0.05}[kind] * span_h
        lookroom = {"med": 0.12, "mcu": 0.1, "cu": 0.06}[kind] * (W / zoom)
        return hx + facing * lookroom, hy + off_y, zoom
    if kind == "ots":
        a, b = arg.split(">")
        return frame_for("mcu:" + b, states)
    return 0, -270, W / 1300

# ───────────────────────────────────────────────────────────── drawing
def draw_rig(c, name, x, gy, st, zoom):
    """draw one character, with the vehicle / bed it needs underneath."""
    base = st.get("base")
    if st["pose"].get("cyclo") and st["pose"]["cyclo"] > 0.5:
        g = Ctx(c, zoom)
        spin = st["t"] * 7 if st.get("moving") else 0
        c.save(); c.translate(x, gy); c.scale(st["scale"], st["scale"])
        S.draw_cyclo(g, 0, 0, face=st["facing"], t=st["t"], spin=spin)
        c.restore()
    RIGS[name].draw(c, zoom * st["scale"], x, gy, st)

def apply_cam(c, cam, par=1.0, center=0.0):
    cx, cy, zoom = cam
    c.translate(W / 2, H / 2)
    c.scale(zoom, zoom)
    c.translate(-(cx * par + center * (1 - par)), -cy)

def draw_set(c, t, st_obj, cam, states, blur=0.0, fg_char=None, under=None):
    cx, cy, zoom = cam
    items = []
    for (d, fn, par) in st_obj.layers():
        items.append((d, "L", fn, par))
    for n, v in states.items():
        if v[3] and n != fg_char:
            items.append((v[1] + 0.001, "C", n, 1.0))
    items.sort(key=lambda a: -a[0])
    far = [it for it in items if it[0] > 0.75 and it[1] == "L"]
    near = [it for it in items if not (it[0] > 0.75 and it[1] == "L")]
    if blur > 0.3:
        c.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(blur, blur)))
    for it in far:
        c.save(); apply_cam(c, cam, it[3], st_obj.center); it[2](Ctx(c, zoom), t); c.restore()
    if blur > 0.3:
        c.restore()
    for it in near:
        c.save(); apply_cam(c, cam, it[3] if it[1] == "L" else 1.0, st_obj.center)
        if it[1] == "L":
            it[2](Ctx(c, zoom), t)
        else:
            n = it[2]
            x, d, st, vis = states[n]
            if st["pose"].get("bed") and hasattr(st_obj, "under"):
                st_obj.under(Ctx(c, zoom), t, x)
            if under:
                under(Ctx(c, zoom), n, x, S.depth_y(d), st)
            draw_rig(c, n, x, S.depth_y(d), st, zoom)
        c.restore()

def draw_fg_char(c, n, states, cam, side):
    x, d, st, vis = states[n]
    st = dict(st); st["mouth"] = (None, 0); st["shadow"] = False
    cx, cy, zoom = cam
    z = zoom * 1.25
    c.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(5, 5)))
    c.save()
    hx = W * (0.04 if side < 0 else 0.96)
    rig = RIGS[n]
    J = rig.skeleton(st["pose"], st["t"])
    c.translate(hx, H * 0.62)
    c.scale(z, z)
    c.translate(-J["head"][0] * st["facing"], -J["head"][1])
    st["scale"] = 1.0
    rig.draw(c, z, 0, 0, st)
    c.restore()
    c.restore()

def grade(c, strength=1.0, warm="#ffcf8a"):
    p = skia.Paint(AntiAlias=True)
    p.setShader(rad_grad((W / 2, H / 2), W * 0.72, [skia.Color(0, 0, 0, 0), skia.Color(20, 10, 4, int(120 * strength))],
                         [0.55, 1.0]))
    c.drawRect(skia.Rect.MakeWH(W, H), p)
    wp = skia.Paint(Color=rgb(warm, int(22 * strength)))
    wp.setBlendMode(skia.BlendMode.kSoftLight)
    c.drawRect(skia.Rect.MakeWH(W, H), wp)

def rain(c, t, strength=1.0, seed=3):
    rng = random.Random(seed)
    p = skia.Paint(AntiAlias=True, Color=skia.Color(210, 220, 235, int(110 * strength)))
    p.setStrokeWidth(1.6); p.setStyle(skia.Paint.kStroke_Style)
    for i in range(int(170 * strength)):
        bx, by = rng.uniform(0, W + 200), rng.uniform(0, H)
        sp = rng.uniform(1300, 1900)
        y = (by + t * sp) % (H + 80) - 40
        x = (bx - (y * 0.18)) % (W + 100) - 50
        c.drawLine(x, y, x - 7, y + 38, p)

def tod_grade(c, tod, lamps=(), cam=None, indoor=True):
    """lighting for the time of day, with lamp glows (world coords) at night."""
    if tod in ("night", "dusk_rain"):
        dark = skia.Paint(Color=rgb("#1a2448", 118 if tod == "night" else 80))
        dark.setBlendMode(skia.BlendMode.kMultiply)
        c.drawRect(skia.Rect.MakeWH(W, H), dark)
        dark2 = skia.Paint(Color=rgb("#070a18", 34 if tod == "night" else 16))
        c.drawRect(skia.Rect.MakeWH(W, H), dark2)
        if cam and lamps:
            cx, cy, zoom = cam
            for (lx, ly, lr) in lamps:
                sx, sy = W / 2 + (lx - cx) * zoom, H / 2 + (ly - cy) * zoom
                r = lr * zoom
                gp = skia.Paint(AntiAlias=True)
                gp.setShader(rad_grad((sx, sy), r, [skia.Color(255, 196, 120, 150), skia.Color(255, 170, 90, 0)]))
                gp.setBlendMode(skia.BlendMode.kScreen)
                c.drawCircle(sx, sy, r, gp)
    elif tod in ("dusk", "evening"):
        wp = skia.Paint(Color=rgb("#e0784a", 60)); wp.setBlendMode(skia.BlendMode.kSoftLight)
        c.drawRect(skia.Rect.MakeWH(W, H), wp)
        c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=rgb("#2a1830", 40)))
    elif tod == "dawn":
        wp = skia.Paint(Color=rgb("#f0a070", 55)); wp.setBlendMode(skia.BlendMode.kSoftLight)
        c.drawRect(skia.Rect.MakeWH(W, H), wp)
    elif tod == "grey":
        c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=rgb("#8a929a", 60)))

def dust(c, t, zoom):
    rng = random.Random(21)
    p = skia.Paint(AntiAlias=True, Color=skia.Color(255, 240, 200, 60))
    for i in range(34):
        bx, by = rng.uniform(0, W), rng.uniform(0, H)
        sp = rng.uniform(4, 14)
        x = (bx + math.sin(t * 0.3 + i) * 30 + t * sp) % W
        y = (by + math.cos(t * 0.21 + i * 1.7) * 20 - t * sp * 0.4) % H
        c.drawCircle(x, y, rng.uniform(1.0, 2.4) * max(1, zoom / 6) ** 0.3, p)

def flash(c, a):
    if a > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=skia.Color(255, 255, 255, int(255 * min(1, a)))))

def black(c, a):
    if a > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=skia.Color(0, 0, 0, int(255 * min(1, a)))))

# ───────────────────────────────────────────────────────────── inserts
def ins_scene(c, t, u, loc, tod, cam0, cam1, chars, shot, extra=None, extra_back=None, grade_tod=None, blur=0.0):
    """Draw a set with an interpolated camera (cx, cy, span) and a list of posed characters:
    chars: [(name, x, d, pose, facing, opts)] opts: walk(bool), expr, look, x1 (walk target), extra (pose overrides)"""
    so = S.get_set(loc, tod)
    k = ease(u)
    cx, cy, span = (lerp(cam0[i], cam1[i], k) for i in range(3))
    cam = (cx, cy, W / span)
    states = {}
    for (n, x, d, pose, facing, o) in chars:
        xx = x
        if "x1" in o:
            xx = lerp(x, o["x1"], o.get("ease", False) and ease(u) or u)
        st = simple_state(n, t, pose, facing, o.get("expr", "neutral"), shot, o.get("look", (0.45, 0.0)),
                          o.get("walk", False), S.depth_scale(d), o.get("speed", 1.7), o.get("extra"))
        st["base"] = pose; st["moving"] = o.get("ride", False)
        st["shadow"] = not st["pose"].get("lie")
        states[n] = (xx, d, st, True)
    if extra_back:
        c.save(); apply_cam(c, cam); extra_back(Ctx(c, cam[2]), t, u); c.restore()
    draw_set(c, t, so, cam, states, blur=blur)
    if extra:
        c.save(); apply_cam(c, cam); extra(Ctx(c, cam[2]), t, u); c.restore()
    tod_grade(c, grade_tod or tod, getattr(so, "lamps", []), cam)
    return cam

def custom(c, t, u, cam0, cam1, fn):
    k = ease(u)
    cx, cy, span = (lerp(cam0[i], cam1[i], k) for i in range(3))
    cam = (cx, cy, W / span)
    c.save(); apply_cam(c, cam); fn(Ctx(c, cam[2]), t, u, cam); c.restore()
    return cam

def seated_rig(c, g, name, x, y, t, shot, facing=1, expr="neutral", look=(0.45, 0.0), pose="sit"):
    st = simple_state(name, t, pose, facing, expr, shot, look)
    st["shadow"] = False
    RIGS[name].draw(c, g.zoom, x, y, st)

def draw_train(g, t, u, shot):
    c = g.c
    S.sky(c, -3000, -1400, 3000, -150, ["#8fc3dc", "#d9ead8", "#f5e6c0"])
    off = t * 160
    for k in range(30):
        x = (k * 260 - off * 0.3) % 5200 - 2600
        g.circle(x, -150, 80 + 25 * math.sin(k * 1.3), "#6a8a52", outline=False)
    for k in range(10):
        x = (k * 560 - off * 0.6) % 5600 - 2800
        S.sugar_palm(g, x, -120, 0.9, t, outline=False)
    S.sky(c, -3000, -150, 3000, 600, ["#c7b27a", "#a89658"])
    for k in range(40):
        x = (k * 150 - off * 1.4) % 6000 - 3000
        g.line([(x, -40), (x + 20, 200)], color="#8a7a4a", w=3, alpha=120)
    # embankment + rails
    c.drawRect(S.R(-3000, 60, 3000, 130), g.fill("#8a7a62"))
    g.line([(-3000, 62), (3000, 62)], color="#4a4642", w=5)
    for k in range(80):
        x = (k * 60 - off * 1.6) % 4800 - 2400
        c.drawRect(S.R(x, 62, x + 22, 76), g.fill("#5a4632"))
    # carriage with an open window: Sam and Soy
    cx0 = -60
    body = S.R(cx0 - 620, -330, cx0 + 620, 40)
    c.drawRRect(skia.RRect.MakeRectXY(body, 18, 18), g.fill("#6a2e24"))
    c.drawRRect(skia.RRect.MakeRectXY(body, 18, 18), g.stroke(OUTLINE, g.lw()))
    c.drawRect(S.R(cx0 - 620, -350, cx0 + 620, -320), g.fill("#3a3632"))
    for k in range(5):
        wx = cx0 - 560 + k * 240
        c.drawRect(S.R(wx, -270, wx + 170, -120), g.fill("#3a2a22"))
    wx = cx0 - 80
    win = S.R(wx, -270, wx + 300, -110)
    c.drawRect(win, g.fill("#4a3a30"))
    c.save(); c.clipRect(win)
    for (n, x, f, e) in (("sam", wx + 110, 1, "hopeful"), ("soy", wx + 210, -1, "worried")):
        st = simple_state(n, t, "stand", f, "calm" if n == "sam" else "worried", shot, (0.5, 0.0))
        st["shadow"] = False
        RIGS[n].draw(c, g.zoom, x, -45 + math.sin(t * 9) * 1.2, st)
    c.restore()
    c.drawRect(win, g.stroke("#2a1a12", 6))
    for k in range(2):
        wheelx = cx0 - 460 + k * 920
        for j in (-60, 60):
            S.wheel(g, wheelx + j, 40, 34, t * 9)
    # steam
    for k in range(6):
        yy = -420 - k * 50
        xx = cx0 + 760 - ((t * 200 + k * 90) % 900)
        S.blob(c, xx, yy, 160 + k * 30, 80, "#f4f2ec", int(150 - k * 18), 22)

def draw_fine_slip(g, t, u, shot, cam):
    c = g.c
    S.sky(c, -2000, -2000, 2000, 2000, ["#8a7a62", "#6a5a48"])
    S.blob(c, 0, -60, 1400, 500, "#a89878", 120, 90)
    skin = CAST["sam"]["skin"]
    # paper slip
    c.save(); c.rotate(-4)
    g.shape(rrect(-190, -150, 380, 250, 6), "#f2ecd8")
    g.shape(rrect(-170, -128, 150, 26, 3), "#b3312c")
    for k in range(6):
        g.line([(-170, -80 + k * 28), (170 - (k % 3) * 40, -80 + k * 28)], color="#8a8270", w=4)
    g.circle(120, 50, 34, "#6a3f6e", alpha=150)
    c.restore()
    for sx in (-1, 1):
        hand = smooth([(sx * 330, 120), (sx * 210, 60), (sx * 170, -40), (sx * 205, -60), (sx * 250, -10),
                       (sx * 290, -30), (sx * 380, 40), (sx * 420, 200)], tension=0.45)
        g.shape(hand, skin if sx < 0 else shade(skin, 0.08))
    for k in range(3):
        g.circle(-60 + k * 40, 150 + (k % 2) * 8, 18, "#b8a878")

def draw_cup_drop(g, t, u, shot, cam):
    c = g.c
    S.tile_floor(g, -1500, 1500, -600, 600, a="#cfc2a6", b="#a89878")
    k = min(1, u / 0.45)
    if u < 0.45:
        y = -520 + k * k * 520
        c.save(); c.translate(0, y); c.rotate(k * 120)
        g.shape(rrect(-40, -50, 80, 100, 14), "#eef0f0")
        c.restore()
    else:
        rng = random.Random(4)
        for i in range(9):
            a = rng.uniform(math.pi, 2 * math.pi)
            dist = (u - 0.45) * 700 * rng.uniform(0.4, 1.0)
            x, y = math.cos(a) * dist, 10 + math.sin(a) * dist * 0.25
            c.save(); c.translate(x, y); c.rotate(rng.uniform(0, 360))
            g.shape(poly([(-16, -8), (18, -4), (6, 12)]), "#eef0f0")
            c.restore()

def draw_court(g, t, u, shot, cam):
    c = g.c
    S.sky(c, -2000, -1400, 2000, -84, ["#6a4a30", "#7d5836"])
    for x in range(-1800, 1800, 240):
        c.drawRect(S.R(x, -1100, x + 30, -84), g.fill("#5a3c24"))
    S.sky(c, -2000, -84, 2000, 600, ["#6a4a30", "#5a3e28"])
    c.drawRect(S.R(-560, -520, 560, -84), g.fill("#4a2c18"))
    g.c.drawRect(S.R(-560, -520, 560, -84), g.stroke(OUTLINE, g.lw()))
    c.drawRect(S.R(-600, -540, 600, -510), g.fill("#6a3f22"))
    # the judge as a dark robed silhouette high up (no face shown)
    g.shape(smooth([(-90, -540), (-80, -700), (0, -760), (80, -700), (90, -540)], tension=0.5), "#1a1410", outline=False)
    g.circle(0, -790, 44, "#1a1410", outline=False)
    # fan
    a = t * 4
    g.line([(0, -1400), (0, -1000)], color="#2a2826", w=5)
    for k in range(3):
        aa = a + k * 2.09
        g.shape(smooth([(0, -1000), (math.cos(aa) * 200, -1000 + math.sin(aa) * 12),
                        (math.cos(aa) * 200, -990 + math.sin(aa) * 12)]), "#3a2a1a")
    # gavel falls at u ~ 0.5
    k = max(0.0, min(1.0, (u - 0.35) / 0.15))
    ang_ = -50 + 50 * k * k
    c.save(); c.translate(260, -540); c.rotate(ang_)
    g.shape(rrect(-6, -120, 12, 110, 3), "#6a3f22")
    g.shape(rrect(-40, -150, 80, 40, 6), "#5a3218")
    c.restore()
    # Sam from behind, small, in the dock
    st = simple_state("sam", t, "head_down", -1, "sad", None)
    RIGS["sam"].draw(c, g.zoom, -300, 200, dict(st, facing=-1))
    c.drawRect(S.R(-420, 60, -180, 220), g.fill("#3a2010"))

def draw_prison_ext(g, t, u, shot, cam, release=False):
    c = g.c
    S.sky(c, -3000, -1400, 3000, -150, ["#9fc4d6", "#dfe8e0"])
    for k in range(3):
        x = (-900 + k * 700 + t * 8) % 3000 - 1500
        S.blob(c, x, -900, 400, 80, "#ffffff", 160, 24)
    c.drawRect(S.R(-2600, -620, 2600, -150), g.fill("#b8b0a0"))
    for x in range(-2600, 2600, 90):
        g.line([(x, -620), (x, -150)], color="#a39a88", w=2)
    c.drawRect(S.R(-2600, -640, 2600, -610), g.fill("#8a8270"))
    # watchtower
    c.drawRect(S.R(760, -900, 900, -620), g.fill("#a39a88"))
    g.shape(poly([(740, -900), (830, -980), (920, -900)]), "#6a625a")
    # gate
    open_ = min(1, u * 2) if release else 0
    c.drawRect(S.R(-220, -520, 220, -150), g.fill("#2a2826"))
    for sd in (-1, 1):
        x0 = sd * (10 + open_ * 200)
        g.shape(rrect(min(x0, x0 + sd * 200), -510, 200, 360, 2), "#4a4642")
        for k in range(6):
            xx = min(x0, x0 + sd * 200) + 20 + k * 32
            g.line([(xx, -500), (xx, -160)], color="#2a2826", w=5)
    S.sky(c, -3000, -150, 3000, 600, ["#c8b894", "#b3a07a"])

def draw_villa_ext(g, t, u, shot, cam, tod="day"):
    c = g.c
    T = S.TOD.get(tod, S.TOD["day"])
    S.sky(c, -3000, -1500, 3000, -150, T["sky"])
    S.coconut(g, -1200, -150, 1.4, t)
    S.coconut(g, 1150, -150, 1.3, t, lean=-18)
    wall = "#efe3c8" if tod == "day" else "#b8b0a0"
    c.drawRect(S.R(-800, -820, 800, -200), g.fill(wall))
    g.c.drawRect(S.R(-800, -820, 800, -200), g.stroke(OUTLINE, g.lw()))
    g.shape(poly([(-860, -820), (0, -1000), (860, -820)]), "#a0522d")
    c.drawRect(S.R(-800, -520, 800, -490), g.fill(shade(wall, 0.12)))
    for x in (-680, -380, 180, 480):
        lit = tod in ("night", "dusk_rain") and x in (-380, 180)
        cols = ("#ffd890", "#f0b060") if lit else ("#6f8a74", "#5a7a64")
        S.barred_window(g, x, -760, 140, 200, t, bright=cols, bars=2, frame="#5a3c24")
        S.barred_window(g, x, -440, 140, 200, t, bright=cols, bars=2, frame="#5a3c24")
        if lit:
            S.glow(c, x + 70, -660, 260, (255, 200, 120), 80)
    c.drawRect(S.R(-120, -440, 120, -200), g.fill("#3a2616"))
    # iron fence + gate
    S.sky(c, -3000, -200, 3000, 600, ["#b8a888", "#a89878"] if tod == "day" else ["#4a4640", "#3a3632"])
    c.drawRect(S.R(-3000, -300, 3000, -284), g.fill("#2a2826"))
    for x in range(-3000, 3000, 40):
        if -150 < x < 150:
            continue
        g.line([(x, -300), (x, -120)], color="#2a2826", w=5)
        g.shape(poly([(x - 6, -300), (x, -318), (x + 6, -300)]), "#2a2826", outline=False)
    for x in (-170, 170):
        c.drawRect(S.R(x - 26, -380, x + 26, -120), g.fill("#d9cbb0"))
        g.c.drawRect(S.R(x - 26, -380, x + 26, -120), g.stroke(OUTLINE, g.lw()))

def draw_river(g, t, u, shot, cam):
    c = g.c
    S.sky(c, -3000, -1500, 3000, -120, ["#060a18", "#101a36", "#1e2a4a"])
    rng = random.Random(9)
    for _ in range(90):
        x = rng.uniform(-2400, 2400); y = rng.uniform(-1400, -300)
        c.drawCircle(x, y, rng.uniform(1, 2.4), skia.Paint(AntiAlias=True, Color=skia.Color(255, 250, 230, 170)))
    g.circle(-900, -1000, 40, "#f4efd8", outline=False, alpha=220)
    # far bank with a few lamps
    for k in range(30):
        g.circle(-2400 + k * 170, -120, 60 + 20 * math.sin(k), "#0a0f1a", outline=False)
    for x in (-700, 300, 1100):
        S.glow(c, x, -140, 60, (255, 200, 120), 160)
    S.sky(c, -3000, -120, 3000, 600, ["#0e1830", "#16223e", "#0a1020"])
    for k in range(40):
        x = (k * 130 + t * 30) % 5200 - 2600
        y = -100 + (k * 37) % 600
        g.line([(x, y), (x + 60, y)], color="#4a5a7a", w=2, alpha=110)
    # boat
    bx = lerp(-500, 250, u)
    by = 60 + math.sin(t * 1.6) * 5
    c.save(); c.translate(bx, by); c.rotate(math.sin(t * 1.3) * 1.5)
    st = simple_state("soy_preg", t, "lie", 1, "tired", None)
    st["expr"]["eo"] = 0.25; st["shadow"] = False
    RIGS["soy_preg"].draw(c, g.zoom, -60, -6, st)
    g.shape(smooth([(-360, -30), (360, -34), (300, 30), (-300, 30)], tension=0.3), "#4a3020")
    g.line([(-350, -30), (350, -34)], color="#6a4a30", w=6)
    st2 = simple_state("sam", t, "work", 1, "worried", None, extra=dict(torso=18, nsh=90, nel=10, fsh=84, fel=14))
    st2["shadow"] = False
    RIGS["sam"].draw(c, g.zoom, 230, -26, st2)
    g.line([(290, -250), (180, 120)], color="#6a4a30", w=5)
    g.line([(-330, -34), (-330, -110)], color="#3a2a1a", w=3)
    g.shape(rrect(-346, -150, 32, 40, 6), "#f4e2b0", alpha=230)
    c.restore()
    S.glow(c, bx - 330, by - 130, 260, (255, 190, 110), 90)
    for k in range(5):
        g.line([(bx - 330 - 20 + k * 10, by + 40 + k * 14), (bx - 330 + 20 - k * 10, by + 40 + k * 14)],
               color="#f0c070", w=3, alpha=120 - k * 20)

def draw_title(c, u, t):
    S.sky(c, 0, 0, W, H, ["#2d3561", "#c0667a", "#f5b26b", "#fbe3a6"])
    img = card("title")
    if img is not None:
        a = ease(min(1, u * 2.2)) * (1 - ease(max(0, (u - 0.85) / 0.15)))
        c.drawImage(img, (W - img.width()) / 2, (H - img.height()) / 2, skia.SamplingOptions(),
                    skia.Paint(Alphaf=a))

def city_passenger(g, x, d, t):
    """an anonymous passenger seated in a moving background cyclo (not a story character)."""
    sc = S.depth_scale(d)
    c = g.c
    c.save(); c.translate(x, S.depth_y(d)); c.scale(sc, sc)
    S.person_bg(g, 124, -98, 132, 0.0, 77, 1, style="hat", seated=True)
    c.restore()

def draw_insert(c, name, t, shot, u):
    """cut-away shots. Returns the tod used, for grading."""
    sh = shot
    if STORY_ART is not None and name in getattr(STORY_ART, "INSERTS", {}):
        return STORY_ART.INSERTS[name](sys.modules[__name__], c, t, shot, u)
    if name == "village_sunrise":
        ins_scene(c, t, u, "village", "dawn", (-700, -380, 2100), (0, -330, 1700),
                  [("sam", -60, 0.8, "hoe", 1, {})], sh,
                  extra=lambda g, t, u: [g.line([(x, y), (x + 14, y - 8), (x + 28, y)], color="#2a2030", w=3)
                                         for k in range(5) for x, y in [(-300 + k * 60 + t * 90, -600 - k * 18 + math.sin(t * 3 + k) * 8)]])
    elif name == "train":
        if u < 0.45:
            custom(c, t, u, (0, -150, 1500), (0, -160, 1400), lambda g, t, u, cam: draw_train(g, t, u, sh))
        else:
            custom(c, t, (u - 0.45) / 0.55, (90, -190, 560), (90, -190, 500), lambda g, t, u, cam: draw_train(g, t, u, sh))
        grade(c, 0.6)
    elif name == "city_street":
        ins_scene(c, t, u, "street", "day", (-500, -330, 1900), (300, -330, 1900),
                  [("worker3", lerp(-1300, 600, u), 0.55, "cyclo", 1, dict(walk=True, ride=True)),
                   ("sam", lerp(-600, 900, u), 0.2, "cyclo", 1, dict(walk=True, ride=True))], sh,
                  extra=lambda g, t, u: (S.draw_car(g, lerp(1500, -1500, u), 230, L=440, col="#6a2e24", face=-1, spin=-t * 9),
                                         city_passenger(g, lerp(-1300, 600, u), 0.55, t)))
    elif name == "fine_slip":
        custom(c, t, u, (0, 0, 1300), (0, 0, 1150), lambda g, t, u, cam: draw_fine_slip(g, t, u, sh, cam))
    elif name == "temple_ext":
        ins_scene(c, t, u, "temple", "day", (-100, -420, 2300), (-300, -330, 1700),
                  [("soy", -120, 0.12, "sit_work", 1, {}), ("sam", -900, 0.1, "stand", 1, {})], sh)
    elif name == "villa_ext":
        custom(c, t, u, (0, -520, 2300), (0, -520, 2100), lambda g, t, u, cam: draw_villa_ext(g, t, u, sh, cam))
    elif name == "villa_rain":
        custom(c, t, u, (0, -560, 2200), (0, -600, 1900), lambda g, t, u, cam: draw_villa_ext(g, t, u, sh, cam, "night"))
        tod_grade(c, "dusk_rain"); rain(c, t, 1.2)
        flash(c, 0.5 * max(0, 1 - abs(u - 0.55) * 14))
    elif name == "cup_drop":
        custom(c, t, u, (0, -100, 1400), (0, -100, 1300), lambda g, t, u, cam: draw_cup_drop(g, t, u, sh, cam))
        tod_grade(c, "night", [(0, -900, 1400)], (0, -100, W / 1400))
    elif name == "closed_door":
        ins_scene(c, t, u, "villa", "night", (900, -250, 700), (930, -250, 560), [], sh)
        rain(c, t, 0.4)
        black(c, ease(max(0, (u - 0.55) / 0.45)))
    elif name == "black":
        c.clear(rgb("#000000"))
    elif name == "morning_gate":
        def fn(g, t, u, cam):
            draw_villa_ext(g, t, u, sh, cam, "day")
            st = simple_state("soy", t, "stand", -1, "sad", None, walk=True, speed=1.3)
            st["pose"]["head"] = 14
            RIGS["soy"].draw(g.c, g.zoom, lerp(0, -700, u), -120, st)
        custom(c, t, u, (-150, -300, 1000), (-420, -300, 950), fn)
        tod_grade(c, "grey")
    elif name == "night_gate":
        def fn(g, t, u, cam):
            draw_villa_ext(g, t, u, sh, cam, "night")
            st = simple_state("sam", t, "stand", 1, "angry", None, walk=True, speed=1.8)
            RIGS["sam"].draw(g.c, g.zoom, lerp(-1000, -200, u), -120, st)
        cam = custom(c, t, u, (-750, -300, 1000), (-350, -300, 950), fn)
        tod_grade(c, "night", [(-170, -420, 500), (170, -420, 500)], cam)
    elif name == "court":
        custom(c, t, u, (0, -560, 2100), (0, -520, 1800), lambda g, t, u, cam: draw_court(g, t, u, sh, cam))
        grade(c, 1.2)
    elif name == "prison_ext":
        custom(c, t, u, (0, -500, 2400), (0, -480, 2100), lambda g, t, u, cam: draw_prison_ext(g, t, u, sh, cam))
    elif name == "prison_shadow":
        def fn(g, t, u, cam):
            c2 = g.c
            S.sky(c2, -2000, -1200, 2000, 600, ["#4a4640", "#3a3632"])
            for i, (n, x0) in enumerate((("huor", -120), ("suos", 180))):
                st = simple_state(n, t, "arms_up" if i == 0 else "point", 1 if i == 0 else -1, "angry", None)
                c2.saveLayer(None, skia.Paint(ColorFilter=skia.ColorFilters.Blend(skia.Color(10, 8, 6, 200),
                                                                                  skia.BlendMode.kSrcIn),
                                              ImageFilter=skia.ImageFilters.Blur(6, 6)))
                RIGS[n].draw(c2, g.zoom * 2.2, x0 + math.sin(t * 6 + i) * 16, -60, dict(st, scale=2.2))
                c2.restore()
            st = simple_state("sam_prison", t, "sit_sad", 1, "cry", None)
            st["pose"]["head"] = 30
            RIGS["sam_prison"].draw(c2, g.zoom, -500, 300, st)
        custom(c, t, u, (0, -300, 1800), (0, -300, 1650), fn)
        black(c, 0.25)
    elif name == "prison_release":
        def fn(g, t, u, cam):
            draw_prison_ext(g, t, u, sh, cam, release=True)
            gy = -60
            S.draw_cyclo(g, 480, gy + 20, face=-1, t=t, col="#2f5a7a")
            for (n, x, pose, f, o) in (("mey", 580, "stand", -1, {}), ("soy", 280, "stand", -1, {}),
                                       ("sam", lerp(0, 140, min(1, u * 1.5)), "stand", 1, dict(walk=u < 0.66))):
                st = simple_state(n, t, pose, f, "happy", sh, walk=o.get("walk", False), speed=1.2)
                RIGS[n].draw(g.c, g.zoom, x, gy, st)
        custom(c, t, u, (150, -300, 1500), (220, -260, 1250), fn)
    elif name == "pedicab_ride":
        def fn(g, t, u, cam):
            pass
        so = S.get_set("street", "day")
        cxw = lerp(-500, 400, u)
        cam = (cxw + 60, -170, W / 820)
        mx = cxw - 150
        states = {"mey": (mx, 0.15, dict(simple_state("mey", t, "cyclo", 1, "happy", sh, walk=True), base="cyclo",
                                                   moving=True, scale=S.depth_scale(0.15)), True)}
        def under(g, n, x, gy, st):
            pass
        draw_set(c, t, so, cam, states)
        c.save(); apply_cam(c, cam)
        g = Ctx(c, cam[2])
        sc = S.depth_scale(0.15)
        for (n, dx) in (("sam", 96), ("soy", 128)):
            st = simple_state(n, t, "sit", 1, "happy", sh)
            st["shadow"] = False; st["scale"] = sc
            RIGS[n].draw(c, cam[2] * sc, mx + dx * sc, S.depth_y(0.15) + (-92 + 15) * sc, st)
        c.restore()
        # re-draw the hood over the passengers' backs is skipped: they sit in front of it
    elif name == "cyclo_ride":
        ins_scene(c, t, u, "newhome", "day", (-200, -330, 1700), (200, -330, 1700),
                  [("soy", -560, 0.2, "stand", 1, {}),
                   ("sam", -300, 0.1, "cyclo", 1, dict(walk=True, ride=True, x1=1100, expr="happy"))], sh)
    elif name in ("car_hit", "car_hit2"):
        so = S.get_set("street", "day")
        shake = 14 * max(0, 1 - abs(u - 0.62) * 8)
        cam = (0 + math.sin(t * 60) * shake, -300, W / 1500)
        n = "sam" if name == "car_hit" else "sam_ragged"
        if name == "car_hit":
            stt = dict(simple_state(n, t, "cyclo", 1, "shock" if u > 0.4 else "neutral", None, walk=u < 0.6),
                       base="cyclo", moving=u < 0.6, scale=S.depth_scale(0.1))
        else:
            stt = dict(simple_state(n, t, "stand" if u > 0.4 else "stand", 1, "shock" if u > 0.4 else "tired", None,
                                    walk=u < 0.45, speed=1.2), base="stand", scale=S.depth_scale(0.1))
        states = {n: (lerp(-250, -120, min(1, u / 0.6)), 0.1, stt, True)}
        draw_set(c, t, so, cam, states)
        c.save(); apply_cam(c, cam)
        g = Ctx(c, cam[2])
        S.draw_car(g, lerp(1200, 180, min(1, u / 0.62)), 20, L=440, col="#1e1e22" if name == "car_hit2" else "#5a3a2a",
                   face=-1, spin=-t * 10)
        c.restore()
        flash(c, ease(max(0, (u - 0.6) / 0.12)) if u < 0.8 else 1.0)
        black(c, max(0, (u - 0.85) / 0.15))
    elif name == "hospital_bed":
        ins_scene(c, t, u, "ward", "day", (20, -120, 620), (20, -120, 560),
                  [("sam", -80, 0.1, "bed", 1, dict(expr="tired")), ("soy", 160, 0.12, "stand", -1, dict(expr="worried"))], sh)
    elif name == "factory_ext":
        def fn(g, t, u, cam):
            c2 = g.c
            S.sky(c2, -3000, -1500, 3000, -150, S.TOD["dawn"]["sky"])
            S.glow(c2, 700, -300, 600, (255, 200, 120), 110)
            c2.drawRect(S.R(-900, -620, 700, -150), g.fill("#9a5a42"))
            g.c.drawRect(S.R(-900, -620, 700, -150), g.stroke(OUTLINE, g.lw()))
            g.shape(poly([(-940, -620), (-100, -760), (740, -620)]), "#6a6660")
            c2.drawRect(S.R(420, -1100, 520, -620), g.fill("#8a4e38"))
            for k in range(6):
                yy = -1120 - k * 70
                S.blob(c2, 470 + k * 40 + math.sin(t + k) * 10 - (t * 20 % 70), yy, 140 + k * 30, 70, "#d8d4cc",
                       170 - k * 25, 18)
            for x in (-760, -420, -80, 260):
                S.barred_window(g, x, -520, 160, 140, t, bright=("#ffd890", "#f0b060"), bars=3, frame="#3a2a22")
            c2.drawRect(S.R(540, -420, 680, -150), g.fill("#3a2616"))
            S.sky(c2, -3000, -150, 3000, 600, ["#9a8c78", "#8a7c68"])
            st = simple_state("sam", t, "stand", 1, "calm", None, walk=True, speed=1.5)
            RIGS["sam"].draw(c2, g.zoom, lerp(-400, 560, u), -100, st)
        custom(c, t, u, (0, -500, 2300), (80, -480, 2100), fn)
        tod_grade(c, "dawn")
    elif name == "factory_room":
        def fn(g, t, u, cam):
            c2 = g.c
            S.plank_wall(g, -2000, 2000, -1000, -84, col="#9a7a50")
            S.barred_window(g, -120, -560, 260, 220, t, bright=("#f0b070", "#b86a58"), bars=3)
            c2.drawRect(S.R(-150, -340, 170, -322), g.fill("#6a4628"))
            S.sky(c2, -2000, -84, 2000, 600, ["#7a5836", "#6a4a2e"])
            S.mat(g, -500, 400, -20)
            # bottle + flower
            g.shape(rrect(40, -400, 26, 60, 6), "#9fc8b8", alpha=200)
            g.line([(53, -400), (58, -470)], color="#3f6a36", w=3)
            g.circle(60, -478, 13, "#e06a8a")
            g.circle(60, -478, 5, "#f4d03a", outline=False)
            st = simple_state("soy", t, "offer", 1, "happy", sh, extra=dict(prop=None, nsh=84, nel=40))
            RIGS["soy"].draw(c2, g.zoom, -80, -30, st)
            st2 = simple_state("sam", t, "sit", -1, "happy", sh)
            RIGS["sam"].draw(c2, g.zoom, 330, 0, st2)
        custom(c, t, u, (120, -200, 820), (120, -200, 760), fn)
        tod_grade(c, "evening")
    elif name == "job_montage":
        part = min(2, int(u * 3)); uu = u * 3 - part
        def fn(g, t, u, cam):
            c2 = g.c
            if part == 0:
                S.plank_wall(g, -2000, 2000, -1000, -84, col="#8a6a44")
                for k in range(12):
                    g.shape(rrect(-900 + (k % 6) * 150, -84 - 60 - (k // 6) * 60, 140, 58, 16), "#d8cba8")
                pose = "carry"
            elif part == 1:
                S.sky(c2, -2000, -1000, 2000, -84, ["#bfe0ec", "#f3e6c4"])
                for row in range(4):
                    for k in range(7 - row):
                        x = -1000 + k * 76 + row * 38
                        y = -84 - 36 - row * 64
                        g.circle(x, y, 36, "#8a5a34")
                        g.circle(x, y, 26, "#d9b07a")
                        g.c.drawCircle(x, y, 14, g.stroke("#b08050", 2))
                pose = "work"
            else:
                S.sky(c2, -2000, -1000, 2000, -84, ["#9a5a42", "#6a3a2a"])
                op = skia.Path(); op.addRRect(skia.RRect.MakeRectXY(S.R(300, -500, 700, -84), 180, 180))
                c2.drawPath(op, g.fill("#2a1208"))
                S.glow(c2, 500, -200, 300, (255, 140, 60), 180)
                for k in range(20):
                    g.shape(rrect(-900 + (k % 10) * 70, -84 - 34 - (k // 10) * 34, 64, 30, 2), "#b8603a")
                pose = "carry"
            S.sky(c2, -2000, -84, 2000, 600, ["#8a7a62", "#6a5a48"])
            st = simple_state("sam", t, pose, 1, "tired", None, walk=pose == "carry", speed=1.2)
            RIGS["sam"].draw(c2, g.zoom, lerp(-300, 100, uu), 0, st)
            # a gate slides shut over the frame at the end of each part
            k = ease(max(0, (uu - 0.72) / 0.28))
            if k > 0:
                x0 = 1000 - k * 2000
                c2.drawRect(S.R(x0, -1200, 1100, 600), g.fill("#3a3632", 235))
                for j in range(40):
                    g.line([(x0 + j * 50, -1200), (x0 + j * 50, 600)], color="#1a1816", w=8)
        custom(c, t, u, (-60, -190, 1000), (0, -190, 950), fn)
    elif name == "campaign":
        ins_scene(c, t, u, "street", "day", (-200, -330, 1700), (100, -300, 1500),
                  [("mey", -520, 0.3, "stand", 1, dict(expr="happy")),
                   ("worker", 380, 0.25, "stand", -1, dict(expr="happy")),
                   ("worker3", 600, 0.4, "stand", -1, {}),
                   ("sam", -120, 0.12, "offer", 1, dict(expr="hopeful", extra=dict(prop="money"))),
                   ("worker2", 140, 0.15, "stand", -1, dict(expr="calm"))], sh,
                  extra=lambda g, t, u: S.people_bg(g, -1200, 1200, -120, 10, t, seed=11, alpha=160))
    elif name == "river_night":
        custom(c, t, u, (-80, -250, 1800), (60, -220, 1500), lambda g, t, u, cam: draw_river(g, t, u, sh, cam))
    elif name == "funeral":
        def fn(g, t, u, cam):
            c2 = g.c
            S.sky(c2, -2000, -1200, 2000, -84, ["#3a2a1e", "#4a3424"])
            S.sky(c2, -2000, -84, 2000, 600, ["#3a2a1e", "#2a1e14"])
            g.shape(rrect(150, -300, 360, 200, 4), "#5a3218")
            g.shape(rrect(250, -470, 150, 170, 3), "#d9a93c")
            g.shape(rrect(262, -458, 126, 146, 2), "#efe6cf")
            for k in range(5):
                a = k * 1.256
                g.circle(325 + math.cos(a) * 30, -385 + math.sin(a) * 30, 20, "#f4f2ec")
            g.circle(325, -385, 12, "#d9a93c")
            for k in range(3):
                x = 250 + k * 70
                g.line([(x, -300), (x, -350)], color="#8a3a24", w=3)
                g.circle(x, -352, 3, "#ff8a3a", outline=False)
                pts = [(x + 8 * math.sin(t * 0.9 + k + j * 0.7), -356 - j * 22 - (t * 14 % 22)) for j in range(8)]
                g.line(pts, color="#d7d2c8", w=2, alpha=90)
            S.glow(c2, 325, -330, 300, (255, 170, 90), 80)
            st = simple_state("sam_ragged", t, "kneel_sampeah", 1, "sad", None)
            st["expr"]["eo"] = 0.2
            RIGS["sam_ragged"].draw(c2, g.zoom, -100, 0, st)
        custom(c, t, u, (100, -230, 900), (100, -220, 780), fn)
    elif name == "homeless_night":
        so = S.get_set("street", "night")
        cam = (lerp(-600, -560, u), -250, W / 1300)
        st = dict(simple_state("sam_ragged", t, "lie", 1, "tired", None), base="lie")
        st["expr"]["eo"] = 0.15 + 0.8 * ease(max(0, (u - 0.6) / 0.2))
        st2 = dict(simple_state("police", t, "stand", -1, "serious", None, walk=u < 0.55, speed=1.2), base="stand")
        states = {"sam_ragged": (-720, 0.1, st, True), "police": (lerp(-200, -470, min(1, u / 0.55)), 0.15, st2, True)}
        def extra(g, t, u):
            g.c.drawRect(S.R(-1100, -80, -500, -10), g.fill("#8a7a5a"))
        draw_set(c, t, so, cam, states)
        c.save(); apply_cam(c, cam)
        g = Ctx(c, cam[2])
        g.shape(poly([(-1100, -560), (-380, -560), (-330, -500), (-1100, -500)]), "#4a4a42")
        lx = states["police"][0] - 50
        g.line([(lx, -130), (lx, -100)], color="#2a2622", w=3)
        g.shape(rrect(lx - 12, -100, 24, 30, 5), "#f4e2b0")
        c.restore()
        tod_grade(c, "night", [(states["police"][0] - 50, -90, 420), (-600, -380, 260)], cam)
        rain(c, t, 0.9)
    elif name == "market":
        def fn(g, t, u, cam):
            c2 = g.c
            S.sky(c2, -2000, -1200, 2000, -150, ["#8fc3dc", "#f2ead0"])
            S.shophouse(g, -1300, -150, 700, 360, wall="#efd3a3")
            S.shophouse(g, -560, -150, 900, 380, wall="#e6c28e", shutter="#6f7e8a")
            S.people_bg(g, -1400, 1400, -150, 14, t, seed=21, alpha=200)
            S.sky(c2, -2000, -150, 2000, 600, ["#b39c7a", "#9f886a"])
            # food stall with an awning and a steaming pot
            g.shape(poly([(80, -520), (780, -520), (840, -440), (20, -440)]), "#b3312c")
            for k in range(7):
                g.shape(poly([(80 + k * 100, -520), (130 + k * 100, -520), (150 + k * 100, -440), (100 + k * 100, -440)]),
                        "#f1eadb")
            for x in (60, 800):
                g.line([(x, -440), (x, -90)], color="#6b4a2e", w=8)
            g.shape(rrect(40, -220, 780, 26, 3), "#7d5132")
            g.shape(smooth([(200, -222), (190, -300), (300, -320), (410, -300), (400, -222)], tension=0.4), "#3a3632")
            for k in range(4):
                yy = -330 - ((t * 40 + k * 40) % 160)
                S.blob(c2, 300 + math.sin(t + k) * 20, yy, 90, 50, "#f4f2ec", int(120 - (-330 - yy) * 0.6), 16)
            for k in range(4):
                g.shape(smooth([(480 + k * 70, -222), (478 + k * 70, -246), (530 + k * 70, -246), (528 + k * 70, -222)]),
                        "#f4f2ec")
            st = simple_state("sam_ragged", t, "stand", 1, "tired", sh, look=(0.5, 0.2))
            RIGS["sam_ragged"].draw(c2, g.zoom, -250, 0, st)
        custom(c, t, u, (-60, -220, 820), (-140, -190, 680), fn)
    elif name == "alley":
        def fn(g, t, u, cam):
            c2 = g.c
            S.sky(c2, -2000, -1400, 2000, -84, ["#3c2a55", "#7a4a5a"])
            c2.drawRect(S.R(-2000, -1400, -300, 600), g.fill("#5a4a40"))
            c2.drawRect(S.R(400, -1400, 2000, 600), g.fill("#4a3a32"))
            for y in range(-1300, 0, 60):
                g.line([(-2000, y), (-300, y)], color="#4a3a30", w=2)
                g.line([(400, y + 30), (2000, y + 30)], color="#3a2a22", w=2)
            S.sky(c2, -300, -84, 400, 600, ["#3a3030", "#2a2020"])
            st = simple_state("sam_ragged", t, "sit_sad", 1, "cry", sh, extra=dict(ik_n="hug_n", ik_f="hug_f"))
            RIGS["sam_ragged"].draw(c2, g.zoom, -120, 0, st)
            g.shape(smooth([(-96, -42), (-100, -64), (-74, -72), (-56, -60), (-62, -38)], tension=0.4), "#8a6a9a")
        custom(c, t, u, (-60, -80, 560), (-70, -80, 480), fn)
        tod_grade(c, "dusk")
    elif name == "prison_window":
        ins_scene(c, t, u, "prison", "day", (40, -200, 800), (0, -130, 560),
                  [("sam_ragged", -40, 0.1, "sit_pray", 1, dict(expr="calm"))], sh)
    elif name == "garden":
        def fn(g, t, u, cam):
            c2 = g.c
            S.sky(c2, -2000, -1400, 2000, -150, S.TOD["day"]["sky"])
            draw_villa_ext(g, t, u, sh, (0, 0, 1), "day")
            for k in range(14):
                x = -1300 + k * 200
                g.circle(x, -150, 90, "#4f7a3e", outline=True)
            S.sky(c2, -2000, -150, 2000, 600, ["#8aa860", "#6a8a48"])
            for k in range(10):
                x = -700 + k * 150
                g.line([(x, -40), (x, -110)], color="#3f6a36", w=4)
                g.circle(x, -120, 16, ["#e06a8a", "#f4d03a", "#f0f0f0"][k % 3])
            st = simple_state("sam", t, "offer", 1, "calm", None, extra=dict(prop=None, nsh=60, nel=20))
            x = lerp(-240, -120, u)
            RIGS["sam"].draw(c2, g.zoom, x, 0, st)
            J = RIGS["sam"].skeleton(st["pose"])
            g.shape(rrect(x + 36, -112, 36, 28, 6), "#8a9aa0")
            for k in range(6):
                yy = -88 + ((t * 300 + k * 30) % 90)
                g.line([(x + 76 + k * 3, yy), (x + 78 + k * 3, yy + 8)], color="#bfe0f0", w=2)
        custom(c, t, u, (-60, -300, 1300), (-40, -280, 1150), fn)
    elif name == "final_sunrise":
        so = S.Village("dawn")
        tl = TL()
        sc = next(s for s in tl["scenes"] if s["n"] == shot["scene"])
        su = (t - sc["t0"]) / max(1e-6, sc["t1"] - sc["t0"])        # progress over the whole last scene
        def back(g, t_):
            cc = g.c
            dark = ["#070a18", "#141a36", "#2a2a4a", "#4a3a50"]
            dawn = ["#2d3561", "#c0667a", "#f5b26b", "#fbe3a6"]
            k = ease(min(1, 0.25 + su * 1.8))
            cols = [mix(dark[i], dawn[i], k) for i in range(4)]
            S.sky(cc, -2000, -1300, 2000, -148, cols)
            sy = lerp(-60, -300, ease(su))
            S.glow(cc, 250, sy, 700, (255, 200, 120), int(40 + 120 * k))
            g.circle(250, sy, 72, "#ffd88a", outline=False, alpha=int(80 + 170 * k))
            for kk in range(26):
                x = -1700 + kk * 130
                g.circle(x, -150, 70 + 25 * math.sin(kk * 1.7), mix("#10141e", "#4d5a3e", k), outline=False)
            for x, s_ in ((-980, 1.0), (-760, 0.8), (520, 0.9), (760, 1.05), (1040, 0.85)):
                S.sugar_palm(g, x, -140, s_, t_, col=mix("#10141e", "#3f5a36", k), trunk=mix("#0a0c12", "#4a3a2a", k),
                             outline=False)
            S.sky(cc, -2000, -150, 2000, 600, [mix("#1a1a24", "#b69a62", k), mix("#12121a", "#9c7a4c", k)])
            for y in (-120, -60, 60):
                g.shape(rrect(-2000, y, 4000, 10, 5), mix("#20202a", "#a58a58", k), outline=False)
            # young green rice: hope
            rng = random.Random(3)
            for _ in range(180):
                x = rng.uniform(-1500, 1500); y = rng.uniform(-130, 220)
                g.line([(x, y), (x + rng.uniform(-5, 5), y - rng.uniform(10, 24))], color=mix("#1a2a1a", "#6a9a4a", k),
                       w=2, alpha=200)
        so.back = back
        so.mid = lambda g, t_: None
        cx = lerp(-200, 40, ease(su))
        span = lerp(700, 1500, ease(su))
        cam = (cx, lerp(-150, -300, ease(su)), W / span)
        st = dict(simple_state("sam", t, "stand", 1, "calm", sh, look=(0.6, -0.3),
                               extra=dict(ik_f="chest_f", fhand="fist")), base="stand", scale=1.0)
        states = {"sam": (-260, 0.1, st, True)}
        draw_set(c, t, so, cam, states)
        c.save(); apply_cam(c, cam)
        g = Ctx(c, cam[2])
        g.line([(-236, -150), (-250, 10)], color="#6b4a2e", w=4)
        g.shape(poly([(-262, 6), (-226, 10), (-240, 22)]), "#6a6660")
        c.restore()
        tod_grade(c, "dawn")
    elif name == "title_end":
        draw_title(c, u, t)
    else:
        c.clear(rgb("#20140c"))

# ───────────────────────────────────────────────────────────── one frame
def scene_of(shot):
    return next(s for s in TL()["scenes"] if s["n"] == shot["scene"])

DISSOLVE = float(getattr(config.P, "DISSOLVE", 0.0) or 0.0)   # cross-dissolve between scenes (s), 0 = dip to black

def draw_frame(c, t, shot=None):
    """one frame; with project.DISSOLVE > 0 the scenes cross-dissolve instead of dipping to black."""
    tl = TL()
    if shot is None:
        shot = next(s for s in tl["shots"] if s["t0"] <= t < s["t1"] or s is tl["shots"][-1])
    if DISSOLVE <= 0:
        return _draw_core(c, t, shot)
    scenes = tl["scenes"]
    sc = scene_of(shot)
    k = scenes.index(sc)
    half = DISSOLVE / 2
    other, a = None, 0.0
    if k > 0 and t < sc["t0"] + half and shot is sc["shots"][0]:
        other = scenes[k - 1]["shots"][-1]
        a = 0.5 - (t - sc["t0"]) / DISSOLVE          # weight of the previous scene
    elif k < len(scenes) - 1 and t >= sc["t1"] - half and shot is sc["shots"][-1]:
        other = scenes[k + 1]["shots"][0]
        a = 0.5 - (sc["t1"] - t) / DISSOLVE          # weight of the next scene
    _draw_core(c, t, shot)
    if other is not None and a > 0.001:
        c.saveLayer(None, skia.Paint(Alphaf=ease(min(1.0, a))))
        _draw_core(c, t, other)
        c.restore()

def _draw_core(c, t, shot):
    tl = TL()
    stage = tl["stage"]
    if shot is None:
        shot = next(s for s in tl["shots"] if s["t0"] <= t < s["t1"] or s is tl["shots"][-1])
    scene = scene_of(shot)
    u = min(1.0, max(0.0, (t - shot["t0"]) / max(shot["dur"], 1e-6)))
    c.clear(rgb("#000000"))
    cam_s = shot.get("cam") or "wide"
    mood = {}
    for s2 in scene["shots"]:
        if s2["t0"] > t:
            break
        if s2.get("speaker") and s2["speaker"] != "narrator":
            mood[s2["speaker"]] = s2.get("expr", "neutral")
    from script_data import SCENES
    sc_src = next(s for s in SCENES if s["n"] == scene["n"])
    start_facing = {n: v[3] for n, v in sc_src["start"].items()}
    if cam_s.startswith("insert:"):
        draw_insert(c, cam_s.split(":", 1)[1], t, shot, u)
        grade(c, 0.9)
    else:
        so = S.get_set(scene["loc"], scene["tod"])
        states = {}
        for n in shot["cast"]:
            vis = stage.vis(n, t)
            x, d, st = char_state(n, t, shot, stage, mood, start_facing)
            states[n] = (x, d, st, vis)
        t_ref = shot["t0"] + min(0.6, shot["dur"] * 0.5)
        if not cam_s.startswith("wide"):
            names = [p for p in cam_s.replace(">", ",").split(":", 1)[-1].split(",") if p in CAST]
            for n in names:
                for (m0, m1, a, b) in stage.moves.get(n, []):
                    if m0 <= t_ref <= m1 and m1 > m0:
                        t_ref = max(t_ref, min(m1 + 0.05, shot["t0"] + shot["dur"] * 0.85))
        ref_states = {}
        for n in shot["cast"]:
            x, d, st = char_state(n, t_ref, shot, stage, mood, start_facing)
            ref_states[n] = (x, d, st, stage.vis(n, t_ref))
        if cam_s.startswith("wide"):
            cx, cy, zoom = frame_for("wide", states)
            r0 = frame_for("wide", ref_states)
            cx, cy, zoom = lerp(r0[0], cx, 0.35), r0[1], r0[2]
        else:
            cx, cy, zoom = frame_for(cam_s, ref_states)
        push = 0.035
        if "push-in" in shot.get("act", "") or "push-in" in shot.get("desc", ""):
            push = 0.12
        if scene["music"] in ("tragedy",) or shot.get("kind") == "reaction":
            push = 0.02
        zoom *= 1 + push * ease(u)
        cam = (cx, cy, zoom)
        blur = min(7.0, (zoom - 6) * 0.45) if zoom > 6 else 0.0
        fg = None
        if cam_s.startswith("ots:"):
            fg = cam_s.split(":", 1)[1].split(">")[0]
        draw_set(c, t, so, cam, states, blur=blur, fg_char=fg)
        if zoom < 5 and scene["tod"] in ("day", "dawn", "evening"):
            dust(c, t, zoom)
        if fg and states.get(fg, (0, 0, 0, False))[3]:
            b = cam_s.split(">")[1]
            side = -1 if states[fg][0] < states[b][0] else 1
            draw_fg_char(c, fg, states, cam, side)
        tod_grade(c, scene["tod"], getattr(so, "lamps", []), cam)
        if scene["tod"] == "dusk_rain" or (scene["loc"] == "villa" and scene["tod"] == "night" and scene["n"] == 7):
            rain(c, t, 0.35)
        grade(c, 1.0)
    # chapter card (first 4 s of each chapter's first scene)
    first_of_ch = scene["n"] == min(s["n"] for s in tl["scenes"] if s["ch"] == scene["ch"]) and \
        getattr(config.P, "CHAPTER_CARDS", True)
    if first_of_ch and t - scene["t0"] < 4.6 and scene["ch"] != 12 or (scene["n"] == 20 and t - scene["t0"] < 4.6):
        img = card(f"ch{scene['ch']:02d}")
        if img is not None:
            dt = t - scene["t0"]
            a = ease(min(1, (dt - 0.5) / 0.6)) * (1 - ease(max(0, (dt - 3.8) / 0.7))) if dt > 0.5 else 0
            if a > 0:
                c.drawImage(img, 70, H - 70 - img.height(), skia.SamplingOptions(), skia.Paint(Alphaf=a))
    # scene fades
    a = 0.0
    first, last = scene is tl["scenes"][0], scene is tl["scenes"][-1]
    if t - scene["t0"] < FADE and (DISSOLVE <= 0 or first):
        a = 1 - (t - scene["t0"]) / FADE
    if scene["t1"] - t < FADE and (DISSOLVE <= 0 or last):
        a = max(a, 1 - (scene["t1"] - t) / FADE)
    black(c, max(0.0, a))

# ───────────────────────────────────────────────────────────── encoding
def render_shot(i):
    tl = TL()
    shot = tl["shots"][i]
    os.makedirs(SHOTS_DIR, exist_ok=True)
    os.makedirs(FRAMES_DIR, exist_ok=True)
    out = os.path.join(SHOTS_DIR, f"shot_{i:03d}.mp4")
    f0 = int(round(shot["t0"] * FPS))
    f1 = int(round(shot["t1"] * FPS))
    n = max(1, f1 - f0)
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    surf = skia.Surface(arr)
    c = surf.getCanvas()
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    mid = n // 2
    for k in range(n):
        t = (f0 + k) / FPS
        draw_frame(c, t, shot)
        pr.stdin.write(arr.tobytes())
        if k == mid:
            img = surf.makeImageSnapshot()
            img.save(os.path.join(FRAMES_DIR, f"shot_{i:03d}.jpg"), skia.kJPEG, 82)
    pr.stdin.close()
    pr.wait()
    return i, n

def still(t, path, shot=None):
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    surf = skia.Surface(arr)
    draw_frame(surf.getCanvas(), t, shot)
    surf.makeImageSnapshot().save(path, skia.kJPEG if path.endswith(".jpg") else skia.kPNG)

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "still":
        still(float(sys.argv[2]), sys.argv[3])
    elif cmd == "shotstill":
        tl = TL(); i = int(sys.argv[2]); sh = tl["shots"][i]
        tt = sh["t0"] + sh["dur"] * (float(sys.argv[3]) if len(sys.argv) > 4 else 0.5)
        still(tt, sys.argv[-1], sh)
    elif cmd == "board":
        # storyboard stills for a list of shot ids (or all)
        tl = TL()
        os.makedirs(FRAMES_DIR, exist_ok=True)
        ids = [int(a) for a in sys.argv[2:]] or list(range(len(tl["shots"])))
        for i in ids:
            sh = tl["shots"][i]
            still(sh["t0"] + sh["dur"] * 0.5, os.path.join(FRAMES_DIR, f"shot_{i:03d}.jpg"), sh)
            print("board", i, flush=True)
    elif cmd == "shots":
        from multiprocessing import Pool
        tl = TL()
        ids = [int(a) for a in sys.argv[2:]] or list(range(len(tl["shots"])))
        t0 = time.time()
        with Pool(int(os.environ.get("JOBS", "6"))) as pool:
            for i, n in pool.imap_unordered(render_shot, ids):
                print(f"shot {i:03d} done ({n} frames) {time.time()-t0:.0f}s", flush=True)
        print("ALL SHOTS DONE", flush=True)
