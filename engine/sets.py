# Backgrounds / props for "ព្រះអាទិត្យថ្មីរះលើផែនដីចាស់" (late-1950s Cambodia), drawn in world units (cm).
# Floor of the front stage is y = 0; depth d places things further back: ground_y = -70*d.
# Every location is a Set with parallax layers: (depth, draw_fn, parallax).  No modern objects, no text.
import math, random
import skia
from gfx import Ctx, rgb, mix, shade, light, poly, smooth, rrect, lin_grad, rad_grad, OUTLINE

def depth_y(d):
    return -70.0 * d

def depth_scale(d):
    return 1.0 - 0.15 * d

def R(x0, y0, x1, y1):
    return skia.Rect.MakeLTRB(x0, y0, x1, y1)

def sky(c, x0, y0, x1, y1, cols, pos=None):
    p = skia.Paint(AntiAlias=True)
    p.setShader(lin_grad((0, y0), (0, y1), cols, pos))
    c.drawRect(R(x0, y0, x1, y1), p)

def blob(c, x, y, w, h, col, a, blur):
    p = skia.Paint(AntiAlias=True, Color=rgb(col, a))
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    c.drawOval(skia.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h), p)

def glow(c, x, y, r, col=(255, 205, 120), a=90):
    p = skia.Paint(AntiAlias=True)
    p.setShader(rad_grad((x, y), r, [skia.Color(*col, a), skia.Color(*col, 0)]))
    c.drawCircle(x, y, r, p)

# time-of-day palettes: sky top/mid/bottom, ground, light tint
TOD = {
    "dawn":      dict(sky=["#2d3561", "#c0667a", "#f5b26b", "#fbe3a6"], ground="#9c7a4c", sun=(1, 0.2)),
    "day":       dict(sky=["#8fc3dc", "#cfe6ea", "#f2ead0"], ground="#c9ae84", sun=None),
    "evening":   dict(sky=["#3a3a6a", "#b86a58", "#f0b070"], ground="#8a6a48", sun=None),
    "dusk":      dict(sky=["#3c2a55", "#b7566a", "#f2a65a"], ground="#7a5a44", sun=None),
    "dusk_rain": dict(sky=["#3e4652", "#5d6672", "#7c8388"], ground="#5c5248", sun=None),
    "night":     dict(sky=["#0c1226", "#1c2848", "#2e3a58"], ground="#3a3530", sun=None),
}

# ───────────────────────────────────────────────────────────── shared props
def draw_car(g, x, gy, L=430, col="#2e2e30", face=1, t=0.0, spin=0.0):
    """1950s rounded sedan, side view, facing right."""
    c = g.c
    c.save(); c.translate(x, gy); c.scale(face, 1)
    H = L * 0.34; wr = L * 0.083
    body = smooth([(-L * 0.5, -wr * 1.1), (-L * 0.52, -H * 0.5), (-L * 0.42, -H * 0.62), (-L * 0.24, -H * 0.64),
                   (-L * 0.16, -H * 0.98), (L * 0.1, -H * 1.02), (L * 0.2, -H * 0.66), (L * 0.42, -H * 0.6),
                   (L * 0.51, -H * 0.42), (L * 0.5, -wr * 1.1)], tension=0.42)
    g.shape(body, col)
    c.save(); c.clipPath(body, skia.ClipOp.kIntersect, True)
    c.drawRect(R(-L, -H * 0.36, L, 0), g.fill(shade(col, 0.18)))
    c.drawRect(R(-L, -H * 0.44, L, -H * 0.41), g.fill("#d9dde0"))
    c.drawRect(R(-L, -H * 1.1, L, -H * 0.85), g.fill(light(col, 0.1)))
    c.restore()
    c.drawPath(body, g.stroke(OUTLINE, g.lw()))
    win = smooth([(-L * 0.2, -H * 0.66), (-L * 0.13, -H * 0.92), (L * 0.07, -H * 0.95), (L * 0.16, -H * 0.67)], tension=0.3)
    g.shape(win, "#a9c3cf")
    g.line([(-L * 0.03, -H * 0.94), (-L * 0.03, -H * 0.66)], color=shade(col, 0.2), w=g.lw() * 2.5)
    g.shape(rrect(-L * 0.1, -H * 0.5, L * 0.05, H * 0.03, 2), "#d9dde0")
    for wx in (-L * 0.3, L * 0.3):
        g.circle(wx, -wr, wr * 1.05, "#1f1d1c")
        g.circle(wx, -wr, wr * 0.62, "#efeee8", outline=False)
        g.circle(wx, -wr, wr * 0.48, "#b9bcbf")
        for k in range(4):
            a = spin + k * math.pi / 2
            g.line([(wx, -wr), (wx + math.cos(a) * wr * 0.45, -wr + math.sin(a) * wr * 0.45)], color="#8a8d90", w=2)
    g.shape(rrect(L * 0.44, -wr * 1.45, L * 0.1, wr * 0.35, 3), "#dfe3e6")
    g.circle(L * 0.47, -H * 0.5, L * 0.028, "#fff6d0")
    g.shape(rrect(-L * 0.54, -wr * 1.45, L * 0.1, wr * 0.35, 3), "#dfe3e6")
    g.circle(-L * 0.5, -H * 0.52, L * 0.02, "#c9423a")
    c.restore()

def wheel(g, x, y, r, spin, rim="#2a2522"):
    g.circle(x, y, r, rim)
    g.c.drawCircle(x, y, r * 0.8, g.stroke("#6a625a", g.lw() * 0.8))
    for k in range(8):
        a = spin + k * math.pi / 8 * 2
        g.line([(x, y), (x + math.cos(a) * r * 0.8, y + math.sin(a) * r * 0.8)], color="#8a8278", w=g.lw() * 0.6)
    g.circle(x, y, r * 0.12, "#8a8278")

def draw_cyclo(g, x, gy, face=1, t=0.0, spin=0.0, col="#9a2f2a", passenger_side=True):
    """Phnom Penh cyclo (1950s): passenger seat in front, driver saddle behind over the rear wheel.
    The driver's pelvis sits at (x, gy-92) (see chars 'cyclo' pose). Facing right."""
    c = g.c
    c.save(); c.translate(x, gy); c.scale(face, 1)
    frame, chrome = "#2e2b28", "#c9ccce"
    # far front wheel (slightly offset, darker) then the near wheels
    wheel(g, 124, -32, 30, spin + 0.4, rim="#1c1a18")
    wheel(g, -6, -34, 32, spin)
    # frame: saddle post, down tube to crank, twin top tubes to the seat carriage, chain stay
    g.line([(0, -88), (8, -34)], color=frame, w=5.5)
    g.line([(8, -34), (-6, -34)], color=frame, w=4.5)
    g.line([(2, -80), (78, -56)], color=frame, w=5.5)
    g.line([(8, -34), (78, -44)], color=frame, w=5.5)
    g.line([(-6, -34), (8, -34)], color="#6a6560", w=2)
    g.line([(-6, -40), (8, -40)], color="#6a6560", w=1.4)          # chain
    # crank + pedals
    ca = spin * 0.8
    for k in (0, math.pi):
        px, py = 8 + math.cos(ca + k) * 12, -34 + math.sin(ca + k) * 12
        g.line([(8, -34), (px, py)], color="#5a5550", w=3)
        g.shape(rrect(px - 6, py - 1.8, 12, 3.6, 1), "#1e1c1a")
    g.circle(8, -34, 5.5, "#8a8580")
    # saddle
    g.shape(smooth([(-13, -93), (12, -95), (17, -88), (-11, -86)], tension=0.4), "#2a1e18")
    # passenger carriage: curved body with a cream stripe, padded seat, backrest, chrome armrail
    body = smooth([(80, -48), (76, -84), (92, -96), (150, -92), (176, -70), (182, -44), (160, -36), (96, -36)],
                  tension=0.45)
    g.shape(body, col)
    c.save(); c.clipPath(body, skia.ClipOp.kIntersect, True)
    c.drawRect(R(60, -66, 200, -60), g.fill("#efe3c8"))
    c.drawRect(R(60, -46, 200, -30), g.fill(shade(col, 0.18)))
    c.restore()
    c.drawPath(body, g.stroke(OUTLINE, g.lw()))
    back = smooth([(80, -86), (74, -128), (86, -138), (100, -132), (104, -92)], tension=0.45)
    g.shape(back, shade(col, 0.08))
    g.shape(rrect(92, -100, 70, 12, 5), light(col, 0.15))               # seat cushion
    g.line([(96, -104), (152, -112), (170, -96)], color=chrome, w=3)    # armrail
    # folded canvas hood: a low pleated bundle resting behind the backrest
    hood = smooth([(62, -118), (60, -140), (72, -150), (92, -146), (100, -130), (96, -118)], tension=0.45)
    g.shape(hood, "#34302c")
    for k in range(3):
        g.line([(64 + k * 2, -126 - k * 7), (97 - k * 2, -124 - k * 7)], color="#4e4944", w=1.6)
    g.line([(80, -118), (84, -96)], color="#5a5550", w=2)
    # footboard, mudguard, lamp
    g.shape(rrect(158, -40, 30, 6, 2), "#4a4642")
    mg = skia.Path(); mg.addArc(R(88, -68, 160, 4), 200, 140)
    c.drawPath(mg, g.stroke(shade(col, 0.25), 4))
    g.circle(184, -62, 5, "#f4ecc8")
    # handlebar behind the passenger seat
    g.line([(64, -62), (52, -100)], color=frame, w=4)
    g.line([(40, -102), (62, -98)], color="#1a1816", w=5)
    c.restore()

def person_bg(g, x, gy, hh, t, rng_i, walk_dir=1, alpha=255, style=None, seated=False):
    """a small opaque background passer-by (face, clothes, walking legs); no named character."""
    import random as _r
    rng = _r.Random(rng_i)
    skin = rng.choice(["#b9804d", "#a86d3f", "#c48c5c", "#9e6538", "#c9956a"])
    female = rng.random() < 0.5
    top = rng.choice(["#e9e2cf", "#6d7f55", "#2f5f8a", "#c9772f", "#8f86a8", "#d98f8a", "#f4f2ec", "#7a4a2a"])
    bottom = rng.choice(["#3a2a24", "#4d3a5c", "#7a3a2a", "#2e2a26"]) if female else rng.choice(["#34405c", "#3a3632", "#5b4632"])
    ph = t * 5.2 + rng_i
    sw = math.sin(ph) * 0.22 * hh * 0.1
    hip = gy - hh * 0.46
    if seated:          # sitting: the hips rest on the seat at gy, no legs shown, body higher
        gy = gy + hh * 0.46
        sw = 0
    # legs
    if seated:
        pass
    elif female:
        g.shape(poly([(x - hh * 0.09, hip), (x + hh * 0.09, hip), (x + hh * 0.08, gy - 4), (x - hh * 0.08, gy - 4)]), bottom)
        g.line([(x - 3 + sw, gy - 5), (x - 3 + sw, gy)], color=skin, w=hh * 0.035)
        g.line([(x + 3 - sw, gy - 5), (x + 3 - sw, gy)], color=skin, w=hh * 0.035)
    else:
        for sgn in (1, -1):
            g.limb([(x, hip), (x + sgn * sw * walk_dir, gy - 2)], hh * 0.07, bottom)
    # body + arms
    torso = rrect(x - hh * 0.11, gy - hh * 0.8, hh * 0.22, hh * 0.38, hh * 0.05)
    g.shape(torso, top)
    g.limb([(x + hh * 0.06 * walk_dir, gy - hh * 0.76), (x + (hh * 0.06 - sw) * walk_dir, gy - hh * 0.5)], hh * 0.05, skin)
    # head
    hy = gy - hh * 0.89
    g.circle(x + hh * 0.01 * walk_dir, hy, hh * 0.085, skin)
    g.shape(smooth([(x - hh * 0.085, hy), (x - hh * 0.06, hy - hh * 0.08), (x + hh * 0.06, hy - hh * 0.085),
                    (x + hh * 0.09, hy - hh * 0.02), (x + hh * 0.02, hy - hh * 0.05)], tension=0.4), "#1a1410")
    g.circle(x + hh * 0.045 * walk_dir, hy + hh * 0.005, max(1.2, hh * 0.012), "#1a0d06", outline=False)
    kind = style if style else rng.choice(["none", "none", "hat", "basket", "krama"])
    if kind == "hat":
        g.shape(poly([(x - hh * 0.16, hy - hh * 0.03), (x, hy - hh * 0.17), (x + hh * 0.16, hy - hh * 0.03)]), "#d8c28a")
    elif kind == "basket":
        g.shape(smooth([(x - hh * 0.1, hy - hh * 0.09), (x - hh * 0.12, hy - hh * 0.2), (x + hh * 0.12, hy - hh * 0.2),
                        (x + hh * 0.1, hy - hh * 0.09)], tension=0.3), "#b8904a")
        g.circle(x - hh * 0.03, hy - hh * 0.2, hh * 0.035, "#6a9a4a", outline=False)
        g.circle(x + hh * 0.04, hy - hh * 0.21, hh * 0.03, "#e06a8a", outline=False)
    elif kind == "krama":
        g.shape(poly([(x - hh * 0.1, gy - hh * 0.8), (x + hh * 0.1, gy - hh * 0.8), (x + hh * 0.02, gy - hh * 0.62)]), "#b3312c")

def tree(g, x, gy, s=1.0, t=0.0, col="#5d8a4a"):
    g.line([(x, gy), (x + 6 * s, gy - 160 * s)], color="#6f5234", w=14 * s)
    for k, (dx, dy, r) in enumerate(((0, -190, 70), (-50, -160, 55), (50, -165, 58), (0, -230, 50))):
        g.circle(x + dx * s + 2 * math.sin(t * 0.8 + k), gy + dy * s, r * s, mix(col, "#3f6a36", k * 0.15))

def sugar_palm(g, x, gy, s=1.0, t=0.0, col="#4f7a3e", trunk="#6a5238", outline=True):
    top = (x + 8 * s, gy - 420 * s)
    g.line([(x, gy), (x + 4 * s, gy - 200 * s), top], color=trunk, w=12 * s)
    for k in range(14):
        a = math.radians(-180 + k * 360 / 14 + 3 * math.sin(t * 0.7 + k))
        rr = 70 * s
        tip = (top[0] + math.cos(a) * rr, top[1] + math.sin(a) * rr * 0.8)
        base_l = (top[0] + math.cos(a - 0.25) * 12 * s, top[1] + math.sin(a - 0.25) * 10 * s)
        base_r = (top[0] + math.cos(a + 0.25) * 12 * s, top[1] + math.sin(a + 0.25) * 10 * s)
        g.shape(poly([base_l, tip, base_r]), mix(col, "#2f5a2e", (k % 3) * 0.2), outline=outline)
    g.circle(top[0], top[1], 14 * s, shade(col, 0.2), outline=outline)

def coconut(g, x, gy, s=1.0, t=0.0, col="#5d8a4a", lean=16):
    top = (x + lean * s, gy - 330 * s)
    g.line([(x, gy), (x + lean * 0.3 * s, gy - 170 * s), top], color="#8a6a44", w=11 * s)
    for k, a in enumerate((-165, -130, -95, -60, -25, 200, 15)):
        ra = math.radians(a + 5 * math.sin(t * 0.6 + k))
        tip = (top[0] + math.cos(ra) * 120 * s, top[1] + math.sin(ra) * 50 * s + 50 * s)
        mid = (top[0] + math.cos(ra) * 64 * s, top[1] + math.sin(ra) * 40 * s - 6 * s)
        g.shape(smooth([top, mid, tip, (mid[0], mid[1] + 9 * s)], tension=0.5), mix(col, "#3f6a36", (k % 3) * 0.2))

def shophouse(g, x, gy, w, h, wall="#e8c79a", shutter="#5f7f7a", roof="#a0522d", arcade=True, floors=2):
    c = g.c
    c.drawRect(R(x, gy - h, x + w, gy), g.fill(wall))
    c.drawRect(R(x, gy - h * 0.5 - 6, x + w, gy - h * 0.5 + 6), g.fill(shade(wall, 0.12)))
    g.c.drawRect(R(x, gy - h, x + w, gy), g.stroke(OUTLINE, g.lw()))
    # tiled roof
    g.shape(poly([(x - 18, gy - h), (x + 30, gy - h - 55), (x + w - 30, gy - h - 55), (x + w + 18, gy - h)]), roof)
    for k in range(1, 5):
        yy = gy - h - k * 11
        g.line([(x - 18 + k * 9.6, yy), (x + w + 18 - k * 9.6, yy)], color=shade(roof, 0.2), w=1.2)
    n = max(2, int(w // 120))
    for k in range(n):
        wx = x + 18 + k * (w - 36) / n
        ww = (w - 36) / n - 18
        c.drawRect(R(wx, gy - h + 30, wx + ww, gy - h * 0.5 - 22), g.fill(shade(wall, 0.3)))
        c.drawRect(R(wx, gy - h + 30, wx + ww * 0.5, gy - h * 0.5 - 22), g.fill(shutter))
        c.drawRect(R(wx + ww * 0.5, gy - h + 30, wx + ww, gy - h * 0.5 - 22), g.fill(shade(shutter, 0.1)))
        for j in range(5):
            yy = gy - h + 38 + j * (h * 0.5 - 60) / 5
            g.line([(wx + 2, yy), (wx + ww - 2, yy)], color=shade(shutter, 0.3), w=1.2)
        g.c.drawRect(R(wx, gy - h + 30, wx + ww, gy - h * 0.5 - 22), g.stroke(OUTLINE, g.lw()))
    if arcade:
        for k in range(n):
            ax = x + 12 + k * (w - 24) / n
            aw = (w - 24) / n - 14
            op = skia.Path()
            op.addRRect(skia.RRect.MakeRectXY(R(ax, gy - h * 0.45, ax + aw, gy + 20), aw * 0.45, aw * 0.45))
            c.drawPath(op, g.fill("#3a2c22"))
            c.save(); c.clipPath(op, skia.ClipOp.kIntersect, True)
            c.drawRect(R(ax, gy - h * 0.2, ax + aw, gy), g.fill("#5a4634"))
            c.restore()
    return (x, gy - h, x + w, gy)

def people_bg(g, x0, x1, gy, n, t, seed=1, alpha=255, speed=40, h=(125, 150)):
    """background passers-by walking along the pavement (small, opaque, varied)."""
    rng = random.Random(seed)
    span = x1 - x0
    crowd_ = []
    for i in range(n):
        base = rng.uniform(0, span)
        sp = rng.choice([-1, 1]) * rng.uniform(0.5, 1.0) * speed
        x = x0 + (base + t * sp) % span
        hh = rng.uniform(*h) * 0.98
        crowd_.append((x, hh, i, 1 if sp > 0 else -1))
    for (x, hh, i, d) in sorted(crowd_, key=lambda e: e[1]):
        person_bg(g, x, gy, hh, t, seed * 100 + i, d)

def bicycle(g, x, gy, spin=0.0, col="#2f3a4a"):
    wheel(g, x - 40, gy - 30, 30, spin)
    wheel(g, x + 40, gy - 30, 30, spin)
    g.line([(x - 40, gy - 30), (x - 5, gy - 30), (x + 20, gy - 72), (x - 18, gy - 72), (x - 40, gy - 30)], color=col, w=4)
    g.line([(x - 5, gy - 30), (x - 18, gy - 80)], color=col, w=4)
    g.line([(x + 40, gy - 30), (x + 24, gy - 86)], color=col, w=4)
    g.line([(x + 16, gy - 88), (x + 32, gy - 90)], color="#1a1816", w=4)
    g.shape(rrect(x - 28, gy - 84, 22, 6, 2), "#2a1e18")

def mat(g, x0, x1, y, col="#c9a867"):
    g.shape(poly([(x0, y - 6), (x1, y - 6), (x1 + 10, y + 4), (x0 - 10, y + 4)]), col)
    for k in range(int((x1 - x0) // 14)):
        g.line([(x0 + k * 14, y - 5), (x0 + k * 14 - 4, y + 3)], color=shade(col, 0.18), w=1)

def oil_lamp(g, x, y, t, s=1.0):
    g.shape(smooth([(x - 8 * s, y), (x - 10 * s, y - 10 * s), (x, y - 16 * s), (x + 10 * s, y - 10 * s), (x + 8 * s, y)]), "#b88a3a")
    g.shape(rrect(x - 6 * s, y - 38 * s, 12 * s, 22 * s, 5 * s), "#f4e7c4", alpha=190)
    fl = (5 + 0.8 * math.sin(t * 11)) * s
    g.ellipse(x, y - 26 * s, 2.2 * s, fl, "#ffcf5a", outline=False)

def lantern_hang(g, x, y, t):
    g.line([(x, y - 60), (x, y - 20)], color="#3a2a1a", w=2)
    g.shape(rrect(x - 12, y - 22, 24, 34, 6), "#f4e2b0", alpha=210)
    g.c.drawRect(R(x - 13, y - 24, x + 13, y - 20), g.fill("#4a3a2a"))
    g.c.drawRect(R(x - 13, y + 10, x + 13, y + 14), g.fill("#4a3a2a"))
    g.ellipse(x, y - 4, 3, 6 + math.sin(t * 9), "#ffcf5a", outline=False)

def door(g, x, gy, w=110, h=230, col="#6a4628", open_=0.0):
    c = g.c
    c.drawRect(R(x - 8, gy - h - 8, x + w + 8, gy), g.fill("#4a3018"))
    c.drawRect(R(x, gy - h, x + w, gy), g.fill("#1c140e"))
    ww = w * (1 - open_ * 0.8)
    g.shape(rrect(x, gy - h, ww, h, 2), col)
    for k in range(2):
        g.shape(rrect(x + ww * 0.14, gy - h + 18 + k * h * 0.46, ww * 0.72, h * 0.38, 2), shade(col, 0.1), olw=g.lw() * 0.7)
    g.circle(x + ww * 0.85, gy - h * 0.48, 3.2, "#c9a44a")

def barred_window(g, x, y, w, h, t, bright=("#fff1cf", "#f4ddb0"), bars=5, frame="#5c3e26"):
    c = g.c
    wp = skia.Paint(AntiAlias=True)
    wp.setShader(lin_grad((0, y), (0, y + h), list(bright)))
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), wp)
    for k in range(1, bars):
        g.line([(x + k * w / bars, y), (x + k * w / bars, y + h)], color=frame, w=5)
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), g.stroke(frame, 8))

def light_shaft(c, x0, x1, y0, dx, y1, a=70, col=(255, 236, 190)):
    lp = skia.Paint(AntiAlias=True)
    lp.setShader(lin_grad(((x0 + x1) / 2, y0), ((x0 + x1) / 2 + dx, y1), [skia.Color(*col, a), skia.Color(*col, 0)]))
    c.drawPath(poly([(x0, y0), (x1, y0), (x1 + dx, y1), (x0 + dx, y1)]), lp)

def plank_wall(g, x0, x1, top, bot, col="#7d5836", step=46, dark="#4f3420"):
    sky(g.c, x0, top, x1, bot, [light(col, 0.05), col])
    for x in range(int(x0), int(x1), step):
        g.line([(x, top), (x, bot)], color=dark, w=3)
    rng = random.Random(int(x0) ^ 77)
    for _ in range(30):
        x = rng.uniform(x0, x1); y = rng.uniform(top, bot)
        g.line([(x, y), (x + rng.uniform(10, 30), y + 1)], color=dark, w=1, alpha=110)

def thatch_wall(g, x0, x1, top, bot, col="#b89760"):
    sky(g.c, x0, top, x1, bot, [light(col, 0.08), col, shade(col, 0.1)])
    rng = random.Random(5)
    for row in range(int((bot - top) // 22)):
        y = top + row * 22
        for k in range(int((x1 - x0) // 16)):
            x = x0 + k * 16 + (row % 2) * 8
            g.line([(x, y), (x + rng.uniform(-3, 3), y + 24)], color=shade(col, rng.uniform(0.1, 0.3)), w=1.4, alpha=170)
        g.line([(x0, y + 22), (x1, y + 22)], color=shade(col, 0.28), w=1.6, alpha=160)

def tile_floor(g, x0, x1, y0, y1, a="#d9cdb4", b="#b8a888"):
    sky(g.c, x0, y0, x1, y1, [a, shade(a, 0.08)])
    for j in range(8):
        yy = y0 + (y1 - y0) * (j / 8) ** 1.4
        g.line([(x0, yy), (x1, yy)], color=b, w=1.5, alpha=150)
    for k in range(-24, 25):
        g.line([(k * 60, y0), (k * 60 * 1.9, y1)], color=b, w=1.5, alpha=130)

def plain_floor(g, x0, x1, y0, y1, cols):
    sky(g.c, x0, y0, x1, y1, cols)

def shadow_spots(c, spots, col="#4a4038", a=70):
    for (x, y, w_, h_) in spots:
        op = skia.Paint(AntiAlias=True, Color=rgb(col, a))
        op.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6))
        c.drawOval(skia.Rect.MakeXYWH(x, y, w_, h_), op)

def temple_roof(g, cx, base_y, w, h, col="#b3432c", gold="#d9a93c"):
    """tiered Khmer vihara roof with naga finials, three tiers."""
    for k in range(3):
        ww = w * (1 - k * 0.22)
        yy = base_y - k * h * 0.34
        g.shape(poly([(cx - ww / 2, yy), (cx - ww * 0.28, yy - h * 0.4), (cx + ww * 0.28, yy - h * 0.4),
                      (cx + ww / 2, yy)]), mix(col, "#8a2f20", k * 0.15))
        g.line([(cx - ww / 2, yy), (cx + ww / 2, yy)], color=gold, w=4)
        for sd in (-1, 1):
            fx = cx + sd * ww / 2
            g.shape(smooth([(fx, yy), (fx + sd * 18, yy - 24), (fx + sd * 8, yy - 40), (fx + sd * 2, yy - 14)],
                           tension=0.4), gold)
    g.line([(cx, base_y - h * 1.02), (cx, base_y - h * 1.35)], color=gold, w=5)
    g.circle(cx, base_y - h * 1.36, 5, gold)

def stupa(g, x, gy, s=1.0, col="#e8dcc0"):
    g.shape(poly([(x - 60 * s, gy), (x + 60 * s, gy), (x + 44 * s, gy - 40 * s), (x - 44 * s, gy - 40 * s)]), col)
    g.shape(smooth([(x - 40 * s, gy - 40 * s), (x - 30 * s, gy - 100 * s), (x, gy - 120 * s), (x + 30 * s, gy - 100 * s),
                    (x + 40 * s, gy - 40 * s)], tension=0.4), light(col, 0.05))
    g.shape(poly([(x - 8 * s, gy - 118 * s), (x, gy - 200 * s), (x + 8 * s, gy - 118 * s)]), "#d9a93c")

def stilt_house(g, x0, x1, fl, top_h=200, wall="#8a5e3b", roof="#8b8f7a", thatch=False):
    c = g.c
    for x in range(int(x0) + 20, int(x1), 80):
        c.drawRect(R(x, fl, x + 13, fl + 180), g.fill("#5c3e26"))
    g.shape(rrect(x0, fl - top_h, x1 - x0, top_h, 3), wall)
    for x in range(int(x0), int(x1), 28):
        g.line([(x, fl - top_h), (x, fl)], color=shade(wall, 0.2), w=2)
    rc = "#b79a5e" if thatch else roof
    g.shape(poly([(x0 - 50, fl - top_h + 10), ((x0 + x1) / 2, fl - top_h - 160), (x1 + 50, fl - top_h + 10)]), rc)
    wx = x0 + (x1 - x0) * 0.62
    c.drawRect(R(wx, fl - top_h + 50, wx + 70, fl - top_h + 120), g.fill("#2a1c12"))
    g.c.drawRect(R(wx, fl - top_h + 50, wx + 70, fl - top_h + 120), g.stroke(OUTLINE, g.lw()))

def palette_night(c, x0, y0, x1, y1, a=150):
    c.drawRect(R(x0, y0, x1, y1), skia.Paint(Color=rgb("#0c1024", a)))


# ───────────────────────────────────────────────────────────── location sets
class Set:
    X0, X1 = -1300, 1300
    BY = -84          # back wall / horizon base
    lamps = []        # world-space light sources for night grading: (x, y, r)
    center = 0        # default camera centre x
    def __init__(self, tod="day"):
        self.tod = tod
        self.T = TOD.get(tod, TOD["day"])
    def layers(self):
        L = [(9.0, self.back, 0.86), (1.2, self.mid, 0.95), (0.03, self.front, 1.0)]
        if hasattr(self, "fg"):
            L.append((-0.6, self.fg, 1.08))
        return L
    def mid(self, g, t): pass
    def front(self, g, t): pass
    @property
    def night(self):
        return self.tod in ("night", "dusk_rain")
    def outdoor_sky(self, g, t, horizon=-150):
        c = g.c
        cols = self.T["sky"]
        sky(c, self.X0 - 600, -1200, self.X1 + 600, horizon + 2, cols)
        if self.tod == "night":
            rng = random.Random(2)
            for _ in range(80):
                x = rng.uniform(self.X0, self.X1); y = rng.uniform(-1100, horizon - 150)
                a = int(120 + 100 * math.sin(t * rng.uniform(1, 3) + x))
                g.c.drawCircle(x, y, rng.uniform(0.8, 2), skia.Paint(AntiAlias=True, Color=skia.Color(255, 250, 230, max(0, a))))
            g.circle(520, -760, 36, "#f4efd8", outline=False, alpha=230)
            glow(c, 520, -760, 160, (230, 230, 210), 50)
        elif self.tod in ("day",):
            for k in range(4):
                x = (-900 + k * 520 + t * 6) % 2600 - 1300
                blob(c, x, -820 + k * 40, 300, 70, "#ffffff", 150, 20)


class Village(Set):
    """dry rice fields at dawn, sugar palms, stilt house on the left"""
    def back(self, g, t):
        c = g.c
        self.outdoor_sky(g, t, -150)
        if self.T.get("sun"):
            glow(c, 250, -210, 520, (255, 200, 120), 120)
            g.circle(250, -200, 70, "#ffd88a", outline=False, alpha=235)
        # far tree line
        for k in range(26):
            x = self.X0 - 400 + k * 130
            g.circle(x, -150, 70 + 25 * math.sin(k * 1.7), "#4d5a3e", outline=False, alpha=230)
        for x, s in ((-980, 1.0), (-760, 0.8), (520, 0.9), (760, 1.05), (1040, 0.85)):
            sugar_palm(g, x, -140, s, t, col="#3f5a36", trunk="#4a3a2a", outline=False)
        # fields
        sky(c, self.X0 - 600, -150, self.X1 + 600, 500, ["#b69a62", self.T["ground"], shade(self.T["ground"], 0.15)])
        for k in range(12):
            y = -150 + (k / 12) ** 1.6 * 640
            g.line([(self.X0 - 600, y), (self.X1 + 600, y)], color=shade(self.T["ground"], 0.22), w=2, alpha=150)
        # dykes
        for y in (-120, -60, 60):
            g.shape(rrect(self.X0 - 600, y, self.X1 - self.X0 + 1200, 10, 5), "#a58a58", outline=False)
        # cracks + stubble
        rng = random.Random(8)
        for _ in range(140):
            x = rng.uniform(self.X0, self.X1); y = rng.uniform(-130, 200)
            g.line([(x, y), (x + rng.uniform(-6, 6), y - rng.uniform(4, 12))], color="#8a7a4a", w=1.4, alpha=160)
    def mid(self, g, t):
        stilt_house(g, -1250, -820, -330, 190, thatch=True)
        for k in range(6):
            g.line([(-1250 + k * 8, -140 - k * 32), (-1180 + k * 8, -140 - k * 32)], color="#6b4a2e", w=6)
        # buffalo far away
        bx = 640
        g.c.drawOval(R(bx - 60, -170, bx + 60, -120), g.fill("#3a3530"))
        g.circle(bx + 62, -150, 18, "#3a3530", outline=False)
        g.line([(bx + 58, -166), (bx + 80, -178)], color="#d8d0c0", w=3)
        for dx in (-40, -20, 30, 45):
            g.line([(bx + dx, -125), (bx + dx, -100)], color="#3a3530", w=6)


class Street(Set):
    """Phnom Penh street, late 1950s: arcaded shophouses, pavement with kerb, awnings, passers-by"""
    lamps = [(-600, -380, 260), (500, -380, 260)]
    HOUSES = ((-1500, 420, 330, "#efd3a3", "#6a8f84", "#a0522d"), (-1060, 380, 300, "#e6c28e", "#6f7e8a", "#a0522d"),
              (-660, 460, 350, "#f1dbb3", "#8a6a4a", "#b35a32"), (-180, 400, 310, "#e8cfa0", "#5f7f7a", "#9a4a2a"),
              (240, 480, 340, "#efd3a3", "#7a8a6a", "#a0522d"), (740, 420, 300, "#e2c08c", "#6f7e8a", "#b35a32"),
              (1180, 420, 330, "#f1dbb3", "#6a8f84", "#a0522d"))
    def back(self, g, t):
        c = g.c
        self.outdoor_sky(g, t, -150)
        for (x, w, h, wall, sh, rf) in self.HOUSES:
            shophouse(g, x, -150, w, h, wall=wall, shutter=sh, roof=rf)
            # balcony rail on the upper floor
            yb = -150 - h * 0.5 + 4
            g.shape(rrect(x + 8, yb - 4, w - 16, 5, 2), shade(wall, 0.35))
            for k in range(int((w - 20) // 18)):
                g.line([(x + 14 + k * 18, yb - 26), (x + 14 + k * 18, yb - 4)], color=shade(wall, 0.35), w=2)
            g.line([(x + 10, yb - 26), (x + w - 10, yb - 26)], color=shade(wall, 0.35), w=3)
            # goods and a lantern inside the arcades
            n = max(2, int(w // 120))
            for k in range(n):
                ax = x + 12 + k * (w - 24) / n
                aw = (w - 24) / n - 14
                cx_ = ax + aw / 2
                g.shape(rrect(cx_ - aw * 0.32, -150 - 60, aw * 0.64, 8, 1), "#6b4a2e", outline=False)
                for j in range(4):
                    g.shape(rrect(cx_ - aw * 0.28 + j * aw * 0.15, -150 - 82, aw * 0.1, 22, 3),
                            ["#c9a44a", "#6a9a4a", "#b3312c", "#efe3c8"][(j + k) % 4], outline=False)
                g.line([(cx_, -150 - h * 0.45 + 10), (cx_, -150 - h * 0.45 + 34)], color="#3a2a1a", w=1.5)
                g.shape(rrect(cx_ - 7, -150 - h * 0.45 + 34, 14, 18, 5), "#e0503a", outline=False)
        # striped canvas awnings (no text)
        for (x, w, a_, b_) in ((-640, 300, "#2d4e6b", "#e9e2cf"), (270, 320, "#7a2e24", "#efe3c8"),
                               (770, 240, "#3a5a3a", "#e9e2cf")):
            aw = poly([(x, -330), (x + w, -330), (x + w + 30, -272), (x - 30, -272)])
            g.shape(aw, a_)
            c.save(); c.clipPath(aw, skia.ClipOp.kIntersect, True)
            for k in range(0, int(w + 60), 40):
                c.drawRect(R(x - 30 + k, -340, x - 10 + k, -262), g.fill(b_))
            c.restore()
            c.drawPath(aw, g.stroke(OUTLINE, g.lw()))
            for k in range(0, int(w + 60), 30):
                g.shape(poly([(x - 30 + k, -272), (x - 15 + k, -262), (x + k, -272)]), a_)
            sky(c, x - 30, -272, x + w + 30, -150, [skia.Color(40, 25, 15, 70), skia.Color(40, 25, 15, 0)])
        for x in (-900, 150, 1000):
            coconut(g, x, -150, 1.1, t)
        # pavement with kerb, then the road
        sky(c, self.X0 - 600, -152, self.X1 + 600, -112, ["#cdbfa4", "#bfae90"])
        for x in range(self.X0 - 600, self.X1 + 600, 60):
            g.line([(x, -152), (x - 6, -112)], color="#a89878", w=1.2, alpha=150)
        people_bg(g, -1400, 1400, -128, 22, t, seed=3, h=(140, 165))
        c.drawRect(R(self.X0 - 600, -112, self.X1 + 600, -104), g.fill("#8f8470"))
        c.drawRect(R(self.X0 - 600, -104, self.X1 + 600, -98), g.fill("#6a6050"))
        sky(c, self.X0 - 600, -98, self.X1 + 600, 500, ["#9a8a70", "#a8967a", "#948266"])
        rng = random.Random(12)
        for _ in range(60):
            x = rng.uniform(self.X0 - 500, self.X1 + 500); y = rng.uniform(-80, 300)
            blob(c, x, y, rng.uniform(60, 200), rng.uniform(8, 20), "#7a6a54", rng.randint(18, 40), 6)
        for y in (-40, 150):
            g.line([(self.X0 - 600, y), (self.X1 + 600, y)], color="#8a7a60", w=3, alpha=90)
        for k in range(-12, 13):
            x = k * 220 % 5200 - 2600
            g.shape(rrect(x, 70, 90, 6, 3), "#e2d4b0", outline=False)
    def mid(self, g, t):
        draw_car(g, -760, -100, L=380, col="#3a4a5a", face=1)
        bicycle(g, 720, -96, spin=0)
        for x in (-600, 500):
            g.line([(x, -100), (x, -420)], color="#2a2826", w=7)
            g.line([(x, -420), (x + 40, -440)], color="#2a2826", w=5)
            g.shape(rrect(x + 30, -452, 26, 22, 5), "#f0e0b0", alpha=220)
        # traffic sign (pictogram only)
        g.line([(80, -100), (80, -300)], color="#5a5a5a", w=5)
        g.circle(80, -320, 26, "#b3312c")
        g.shape(rrect(64, -324, 32, 8, 2), "#f4f4f0", outline=False)


class Yard(Set):
    """Madam Kim Leang's cyclo yard"""
    def back(self, g, t):
        c = g.c
        sky(c, self.X0 - 400, -900, self.X1 + 400, -84, ["#e5d4b0", "#d9c49c"])
        c.drawRect(R(self.X0 - 400, -900, self.X1 + 400, -560), g.fill("#8a8f90"))
        for x in range(self.X0 - 400, self.X1 + 400, 26):
            g.line([(x, -900), (x + 20, -560)], color="#a9adae", w=6, alpha=130)
        c.drawRect(R(self.X0 - 400, -570, self.X1 + 400, -545), g.fill("#5c3e26"))
        for x in (-900, -300, 300, 900):
            c.drawRect(R(x - 10, -545, x + 10, -84), g.fill("#6b4a2e"))
        # open side to the bright street
        barred_window(g, 380, -460, 460, 300, t, bars=1)
        shophouse(g, 420, -170, 300, 240, wall="#efd3a3")
        sky(c, self.X0 - 400, -84, self.X1 + 400, 500, ["#9a8c78", "#b3a48c", "#8f8270"])
        shadow_spots(c, ((-300, -20, 180, 18), (200, 30, 120, 14)))
    def mid(self, g, t):
        for x in (-1050, -720, -390):
            draw_cyclo(g, x, -60, face=1, col=["#9a2f2a", "#2f5a7a", "#3f6a3a"][int((x + 1050) // 330) % 3])
        # small table with ledger and cash tin
        g.shape(rrect(560, -150, 170, 10, 2), "#6b4226")
        for x in (570, 715):
            g.line([(x, -140), (x, -70)], color="#5a3c24", w=6)
        g.shape(rrect(590, -162, 60, 12, 2), "#6a2e22")
        g.shape(rrect(665, -166, 36, 16, 3), "#8a8f90")


class Hut(Set):
    """tiny rented hut: palm-leaf walls, bamboo posts, oil lamp"""
    def __init__(self, tod="dusk"):
        super().__init__(tod)
        self.lamps = [(-470, -120, 420)] if self.tod in ("night", "dusk_rain", "dusk") else []
    def back(self, g, t):
        c = g.c
        thatch_wall(g, self.X0 - 400, self.X1 + 400, -700, -84)
        for x in (-760, -200, 380, 900):
            c.drawRect(R(x - 9, -700, x + 9, -84), g.fill("#9a8452"))
            for yy in range(-690, -84, 60):
                g.line([(x - 9, yy), (x + 9, yy)], color="#7a6a3a", w=2)
        # window: rain or night outside
        wx, wy, ww, wh = 120, -420, 200, 150
        out = {"dusk_rain": ("#6d7682", "#8a929a"), "night": ("#1c2848", "#2e3a58"),
               "dusk": ("#e79b62", "#b7566a")}.get(self.tod, ("#fff1cf", "#f4ddb0"))
        barred_window(g, wx, wy, ww, wh, t, bright=out, bars=4, frame="#7a6a3a")
        if self.tod == "dusk_rain":
            c.save(); c.clipRect(skia.Rect.MakeXYWH(wx, wy, ww, wh))
            for k in range(30):
                x = wx + (k * 37 + t * 40) % ww
                y = wy + (k * 53 + t * 900) % wh
                g.line([(x, y), (x - 4, y + 18)], color="#dfe6ee", w=1.4, alpha=150)
            c.restore()
        # door (right)
        door(g, 560, -84, 130, 250, col="#8a7a4a")
        # floor: packed earth with a mat
        sky(c, self.X0 - 400, -84, self.X1 + 400, 500, ["#6a5038", "#5a4230"])
        mat(g, -420, 320, -20, "#c9a867")
    def mid(self, g, t):
        # clay pots, a small shelf with bowls
        g.shape(rrect(-980, -300, 160, 10, 2), "#7a5a32")
        for k in range(3):
            g.shape(smooth([(-970 + k * 50, -300), (-966 + k * 50, -322), (-936 + k * 50, -322), (-932 + k * 50, -300)]),
                    "#e8e0d0")
        if self.tod == "dusk_rain":
            y = -700 + (t * 400) % 610       # a leak dripping from the roof near the wall
            g.ellipse(-860, y, 2.2, 4, "#cfe0ee", outline=False, alpha=200)
    def front(self, g, t):
        oil_lamp(g, -470, -10, t, 1.3)


class Temple(Set):
    """under the eaves of a vihara: columns, raised base, bodhi tree beyond"""
    def back(self, g, t):
        c = g.c
        self.outdoor_sky(g, t, -150)
        tree(g, 820, -150, 1.8, t, col="#4f7a3e")
        stupa(g, 1150, -150, 1.2)
        sky(c, self.X0 - 600, -150, self.X1 + 600, 500, ["#d9c49c", "#c9b08a"])
        # the hall wall with tall windows
        c.drawRect(R(-1400, -560, 520, -84), g.fill("#efe3c8"))
        g.c.drawRect(R(-1400, -560, 520, -84), g.stroke(OUTLINE, g.lw()))
        for x in (-1200, -860, -520, -180, 160):
            c.drawRect(R(x, -470, x + 90, -230), g.fill("#8a3a24"))
            c.drawRect(R(x + 10, -460, x + 44, -240), g.fill("#a9502c"))
            c.drawRect(R(x + 46, -460, x + 80, -240), g.fill("#a9502c"))
            g.shape(poly([(x - 10, -470), (x + 45, -520), (x + 100, -470)]), "#d9a93c")
        # eave overhang
        g.shape(poly([(-1450, -560), (600, -560), (640, -610), (-1450, -610)]), "#b3432c")
        g.line([(-1450, -560), (600, -560)], color="#d9a93c", w=5)
        # raised base + steps
        c.drawRect(R(-1400, -100, 560, -60), g.fill("#d9cbb0"))
        g.c.drawRect(R(-1400, -100, 560, -60), g.stroke(OUTLINE, g.lw()))
        for k in range(3):
            c.drawRect(R(560 + k * 26, -100 + k * 14, 700 - k * 10, -86 + k * 14), g.fill("#cfc0a4"))
    def mid(self, g, t):
        for x in (-1100, -760, -420, -80, 260):
            g.shape(rrect(x, -560, 30, 470, 3), "#f2e8d2")
            g.shape(rrect(x - 8, -120, 46, 24, 2), "#e2d4b8")
            g.shape(rrect(x - 8, -570, 46, 18, 2), "#d9a93c")
    def front(self, g, t):
        mat(g, -500, 20, -2, "#b89a5e")
        g.shape(smooth([(-460, -2), (-470, -40), (-420, -52), (-380, -40), (-390, -2)], tension=0.5), "#3f6e4a")
        g.shape(smooth([(-360, -2), (-366, -30), (-330, -40), (-300, -30), (-306, -2)], tension=0.5), "#8a4a5a")


class Villa(Set):
    """Boss Hok's hall: tiled floor, tall shutters, cabinet, sofa, clock"""
    def __init__(self, tod="day"):
        super().__init__(tod)
        self.lamps = [(-150, -470, 560), (620, -250, 260)] if self.night else []
    def back(self, g, t):
        c = g.c
        sky(c, self.X0 - 400, -900, self.X1 + 400, -84, ["#e9dcc0", "#f3e8d0", "#e2d2b0"])
        c.drawRect(R(self.X0 - 400, -190, self.X1 + 400, -84), g.fill("#b69468"))
        g.line([(self.X0 - 400, -190), (self.X1 + 400, -190)], color="#7a5c3c", w=3)
        for x in (-900, -300, 300):
            out = ("#1c2848", "#2e3a58") if self.night else ("#fff1cf", "#f4ddb0")
            barred_window(g, x, -560, 170, 300, t, bright=out, bars=3, frame="#6a4a2a")
            for sx in (x - 64, x + 176):
                c.drawRect(skia.Rect.MakeXYWH(sx, -566, 58, 312), g.fill("#4f7a6a"))
                for k in range(12):
                    g.line([(sx + 4, -556 + k * 25), (sx + 54, -556 + k * 25)], color="#3a5a4c", w=2.5)
            if self.tod == "night" or self.tod == "dusk_rain":
                c.save(); c.clipRect(skia.Rect.MakeXYWH(x, -560, 170, 300))
                for k in range(40):
                    xx = x + (k * 29 + t * 60) % 170
                    yy = -560 + (k * 71 + t * 1100) % 300
                    g.line([(xx, yy), (xx - 5, yy + 24)], color="#aab6c8", w=1.4, alpha=140)
                c.restore()
        # wall clock (hands only)
        g.circle(620, -520, 34, "#6a3f22"); g.circle(620, -520, 27, "#f4efe2")
        hh = math.radians(-90 + 270) if self.night else math.radians(-90 + 60)
        g.line([(620, -520), (620 + math.cos(hh) * 14, -520 + math.sin(hh) * 14)], w=2.4)
        g.line([(620, -520), (620, -542)], w=1.6)
        # picture frame: river landscape
        c.drawRect(R(-620, -520, -420, -390), g.fill("#6a3f22"))
        sky(c, -610, -510, -430, -400, ["#f0c88a", "#b8d0c8"])
        tile_floor(g, self.X0 - 400, self.X1 + 400, -84, 500)
        door(g, 900, -84, 130, 300, col="#6a4628")
    def mid(self, g, t):
        # cabinet
        x, gy = 440, -80
        g.shape(rrect(x, gy - 230, 150, 230, 3), "#5a3218")
        for k in range(2):
            g.shape(rrect(x + 10 + k * 70, gy - 220, 60, 120, 2), "#6a3f22")
        g.shape(rrect(x + 10, gy - 90, 130, 70, 2), "#6a3f22")
        for k in range(4):
            g.shape(rrect(x + 16 + k * 32, gy - 262, 20, 32, 5), ["#e8e0d0", "#2f5a6e", "#d9a93c", "#e8e0d0"][k])
        # sofa
        g.shape(rrect(-700, -170, 300, 60, 16), "#7a2e24")
        g.shape(rrect(-720, -130, 340, 60, 12), "#8a3a2c")
        for x in (-705, -410):
            g.line([(x, -70), (x, -60)], color="#3a2010", w=6)
    def fg(self, g, t):
        if self.night:
            lantern_hang(g, -150, -520, t)


class MeyHome(Set):
    """Mey and Mom's wooden house by the pedicab stand"""
    def __init__(self, tod="day"):
        super().__init__(tod)
        self.lamps = [(300, -300, 380)] if self.night else []
    def back(self, g, t):
        c = g.c
        plank_wall(g, self.X0 - 400, self.X1 + 400, -760, -84, col="#8a6440")
        c.drawRect(R(self.X0 - 400, -760, self.X1 + 400, -690), g.fill("#5c3e26"))
        out = ("#1c2848", "#2e3a58") if self.night else ("#fff1cf", "#f0d8a6")
        barred_window(g, -120, -430, 180, 150, t, bright=out, bars=4)
        # open doorway with a pedicab outside
        c.drawRect(R(-1060, -400, -820, -84), g.fill(out[0]))
        if not self.night:
            draw_cyclo(g, -1000, -84, face=1, col="#2f5a7a")
        c.drawRect(R(-1070, -410, -810, -400), g.fill("#5c3e26"))
        # shelf, pots, hanging krama
        g.shape(rrect(320, -380, 220, 10, 2), "#6a4628")
        for k in range(4):
            g.shape(smooth([(335 + k * 50, -380), (338 + k * 50, -404), (366 + k * 50, -404), (370 + k * 50, -380)]),
                    ["#e8e0d0", "#a0522d", "#e8e0d0", "#3f6e4a"][k])
        g.line([(600, -520), (760, -520)], color="#3a2a1a", w=2)
        g.shape(poly([(640, -520), (700, -520), (705, -420), (636, -426)]), "#2f5d8a")
        sky(c, self.X0 - 400, -84, self.X1 + 400, 500, ["#7a5836", "#6a4a2e"])
        for k in range(10):
            g.line([(self.X0 - 400, -84 + k * 30), (self.X1 + 400, -84 + k * 30)], color="#5a3c24", w=2, alpha=150)
        mat(g, -450, 450, -20, "#c9a867")
    def front(self, g, t):
        if self.night:
            oil_lamp(g, 300, -12, t, 1.3)


class Prison(Set):
    """a bare cell: stone walls, high barred window with a shaft of light"""
    lamps = []
    def back(self, g, t):
        c = g.c
        sky(c, self.X0 - 400, -900, self.X1 + 400, -84, ["#6f6c66", "#8a8680", "#77736c"])
        rng = random.Random(4)
        for row in range(16):
            y = -900 + row * 52
            off = (row % 2) * 60
            for k in range(-20, 21):
                x = k * 120 + off
                c.drawRect(R(x, y, x + 116, y + 48), g.fill(mix("#7d7972", "#6a6660", rng.random() * 0.6)))
        bright = ("#f8ecd0", "#e8d4a8") if self.tod != "dusk" else ("#e79b62", "#b7566a")
        barred_window(g, 60, -560, 160, 110, t, bright=bright, bars=5, frame="#2a2826")
        sky(c, self.X0 - 400, -84, self.X1 + 400, 500, ["#5a5650", "#6a665e", "#4a4640"])
        light_shaft(c, 60, 220, -450, -300, 60, a=60 if self.tod != "dusk" else 45)
        # bars on the right (cell front)
        for k in range(8):
            x = 700 + k * 44
            g.line([(x, -900), (x, -84)], color="#2a2826", w=9)
        g.line([(690, -620), (1060, -620)], color="#2a2826", w=10)
    def front(self, g, t):
        mat(g, -300, 160, -4, "#8a7a5a")
        g.shape(rrect(420, -40, 60, 40, 6), "#6a665e")


class Visit(Set):
    """visiting room: counter and iron bars; the prisoner stands behind the bars (x > 40)"""
    def back(self, g, t):
        c = g.c
        sky(c, self.X0 - 400, -900, self.X1 + 400, -84, ["#bdb4a0", "#cfc6b0", "#a8a08c"])
        c.drawRect(R(self.X0 - 400, -230, self.X1 + 400, -84), g.fill("#8a8270"))
        barred_window(g, -700, -560, 200, 150, t, bars=5, frame="#3a3632")
        sky(c, self.X0 - 400, -84, self.X1 + 400, 500, ["#8a8270", "#7a7262"])
    def front(self, g, t):
        # counter
        g.shape(rrect(10, -110, 80, 110, 2), "#6a4a2e")
        g.shape(rrect(-10, -122, 120, 14, 2), "#7d5836")
    def fg(self, g, t):
        c = g.c
        for k in range(10):
            x = 60 + k * 38
            g.line([(x, -1000), (x, 60)], color="#2a2826", w=6)
        g.line([(40, -300), (440, -300)], color="#2a2826", w=8)


class NewHome(Set):
    """a small wooden house near Wat Mohamontrei (temple roof beyond)"""
    def back(self, g, t):
        c = g.c
        self.outdoor_sky(g, t, -150)
        temple_roof(g, 800, -300, 520, 300)
        c.drawRect(R(580, -300, 1020, -150), g.fill("#efe3c8"))
        coconut(g, -1000, -150, 1.2, t)
        tree(g, 1150, -150, 1.3, t)
        sky(c, self.X0 - 600, -150, self.X1 + 600, 500, ["#cdb58c", "#b89a6c"])
        stilt_house(g, -760, -160, -330, 200, wall="#8a5e3b", roof="#8b8f7a")
        for k in range(6):
            g.line([(-480 + k * 6, -130 - k * 34), (-400 + k * 6, -130 - k * 34)], color="#6b4a2e", w=6)
        door(g, -520, -330, 90, 170, col="#6a4628")
    def mid(self, g, t):
        g.line([(300, -100), (300, -240)], color="#6b4a2e", w=6)
        g.line([(300, -240), (560, -230)], color="#6b4a2e", w=3)
        for k in range(4):
            g.shape(poly([(330 + k * 50, -234), (360 + k * 50, -233), (356 + k * 50, -190), (334 + k * 50, -192)]),
                    ["#e8e0d0", "#3f6e4a", "#d98f8a", "#e8e0d0"][k])


class Factory(Set):
    """soap factory floor: brick walls, big vats, pulleys, sacks and crates"""
    lamps = []
    def back(self, g, t):
        c = g.c
        sky(c, self.X0 - 400, -1000, self.X1 + 400, -84, ["#9a5a42", "#a8664a", "#8a4e38"])
        for row in range(20):
            y = -1000 + row * 46
            g.line([(self.X0 - 400, y), (self.X1 + 400, y)], color="#7a4230", w=2)
            off = (row % 2) * 45
            for k in range(-32, 33):
                g.line([(k * 90 + off, y), (k * 90 + off, y + 46)], color="#7a4230", w=1.5)
        for x in (-900, -300, 300, 900):
            barred_window(g, x, -760, 220, 180, t, bright=("#f8ecd0", "#e8d4a8"), bars=4, frame="#3a2a22")
            light_shaft(c, x, x + 220, -580, -200, 80, a=40)
        # overhead line shaft with pulleys and belts
        g.line([(self.X0 - 400, -620), (self.X1 + 400, -620)], color="#3a3632", w=10)
        for x in (-640, 0, 640):
            a = t * 3
            g.circle(x, -620, 42, "#4a4642")
            for k in range(4):
                g.line([(x, -620), (x + math.cos(a + k * 1.57) * 38, -620 + math.sin(a + k * 1.57) * 38)],
                       color="#6a665e", w=4)
            g.line([(x - 40, -620), (x - 30, -250)], color="#2a2622", w=4)
            g.line([(x + 40, -620), (x + 30, -250)], color="#2a2622", w=4)
        sky(c, self.X0 - 400, -84, self.X1 + 400, 500, ["#7e7263", "#8f8272", "#6e6254"])
        shadow_spots(c, ((-500, 0, 200, 20), (300, 40, 160, 16), (700, -30, 120, 14)))
    def mid(self, g, t):
        # vats
        for (x, w) in ((-640, 260), (0, 260), (640, 260)):
            g.shape(rrect(x - w / 2, -330, w, 250, 18), "#6a665e")
            g.shape(rrect(x - w / 2 - 10, -340, w + 20, 24, 8), "#8a8680")
            g.c.drawRect(R(x - w / 2 + 10, -300, x + w / 2 - 10, -290), g.fill("#4a4642"))
            for k in range(4):
                yy = -360 - ((t * 30 + k * 40) % 160)
                blob(g.c, x + 30 * math.sin(t * 0.7 + k), yy, 90, 50, "#f4f2ec", int(60 - (-360 - yy) * 0.3), 18)
        # crates of soap bars and sacks
        for k in range(3):
            g.shape(rrect(900 + k * 10, -180 - k * 60, 150, 60, 3), "#a0784a")
            g.line([(905 + k * 10, -150 - k * 60), (1045 + k * 10, -150 - k * 60)], color="#7a5a32", w=2)
        for k in range(4):
            g.shape(smooth([(-1100 + k * 70, -84), (-1110 + k * 70, -140), (-1070 + k * 70, -150),
                            (-1040 + k * 70, -140), (-1050 + k * 70, -84)], tension=0.4), "#d8cba8")


class Hall(Set):
    """plain wooden meeting hall at evening, kerosene lamp"""
    lamps = [(-60, -330, 640)]
    def back(self, g, t):
        c = g.c
        plank_wall(g, self.X0 - 400, self.X1 + 400, -800, -84, col="#7d5836")
        c.drawRect(R(self.X0 - 400, -800, self.X1 + 400, -720), g.fill("#4a3018"))
        barred_window(g, 520, -520, 200, 170, t, bright=("#3a3a6a", "#b86a58"), bars=4)
        # blank notice board with pinned papers (no text)
        g.shape(rrect(-700, -520, 300, 190, 4), "#5a3c24")
        for k in range(5):
            g.shape(rrect(-680 + k * 55, -500 + (k % 2) * 60, 44, 56, 1), "#efe6cf")
        sky(c, self.X0 - 400, -84, self.X1 + 400, 500, ["#6a4a30", "#5a3e28"])
        mat(g, -700, 700, -30, "#b89a5e")
    def front(self, g, t):
        # low table with the membership list in front of Sam
        g.shape(rrect(-40, -40, 110, 10, 2), "#6b4226")
        g.line([(-30, -30), (-30, -2)], color="#5a3c24", w=5)
        g.line([(60, -30), (60, -2)], color="#5a3c24", w=5)
        g.shape(poly([(-24, -42), (14, -46), (48, -42), (46, -40), (-22, -40)]), "#efe6cf")
        oil_lamp(g, 170, -40, t, 1.1)
    def fg(self, g, t):
        lantern_hang(g, -60, -540, t)


class Office(Set):
    """outside a colonial office building; an old car at the kerb"""
    def back(self, g, t):
        c = g.c
        self.outdoor_sky(g, t, -150)
        c.drawRect(R(-1300, -620, 700, -150), g.fill("#f0e2c4"))
        g.c.drawRect(R(-1300, -620, 700, -150), g.stroke(OUTLINE, g.lw()))
        g.shape(poly([(-1340, -620), (-300, -720), (740, -620)]), "#b8a888")
        for x in range(-1200, 640, 170):
            g.shape(rrect(x, -560, 40, 410, 3), "#fbf4e2")
            c.drawRect(R(x + 60, -520, x + 130, -360), g.fill("#6f8a74"))
        g.shape(rrect(-360, -150 - 18, 200, 10, 2), "#c9a44a")  # blank brass plate
        coconut(g, 900, -150, 1.2, t)
        sky(c, self.X0 - 600, -150, self.X1 + 600, -110, ["#c8bca4", "#b8ac94"])
        sky(c, self.X0 - 600, -110, self.X1 + 600, 500, ["#b39c7a", "#9f886a"])
        # iron gate posts
        for x in (-560, 580):
            c.drawRect(R(x - 24, -330, x + 24, -110), g.fill("#e8dcc0"))
            g.c.drawRect(R(x - 24, -330, x + 24, -110), g.stroke(OUTLINE, g.lw()))


class Clinic(Set):
    """dim corridor of a clinic across the river: one lantern, a bench, the treatment-room door"""
    lamps = [(-40, -420, 520)]
    def back(self, g, t):
        c = g.c
        plank_wall(g, self.X0 - 400, self.X1 + 400, -800, -84, col="#9a8a6a", step=60, dark="#6a5a40")
        c.drawRect(R(self.X0 - 400, -210, self.X1 + 400, -84), g.fill("#7a6a50"))
        door(g, 300, -84, 140, 280, col="#e8e0cc")
        sky(c, self.X0 - 400, -84, self.X1 + 400, 500, ["#5a4e40", "#4a4034"])
        barred_window(g, -800, -520, 150, 130, t, bright=("#0c1226", "#1c2848"), bars=3)
    def mid(self, g, t):
        g.shape(rrect(-400, -150, 300, 14, 3), "#6b4226")
        for x in (-390, -115):
            g.line([(x, -136), (x, -84)], color="#5a3c24", w=6)
        # wall lantern
        g.line([(-40, -470), (-40, -430)], color="#3a2a1a", w=3)
        g.shape(rrect(-54, -432, 28, 40, 6), "#f4e2b0", alpha=220)
        g.ellipse(-40, -412, 3, 6 + math.sin(t * 7), "#ffcf5a", outline=False)


class Mansion(Set):
    """the Oknha's grand hall: carved wood, gilded cabinet, red carpet"""
    def back(self, g, t):
        c = g.c
        sky(c, self.X0 - 400, -1000, self.X1 + 400, -84, ["#6a3a22", "#7d4a2c", "#5a3018"])
        for x in range(-1600, 1700, 300):
            g.shape(rrect(x, -760, 240, 560, 6), "#8a5a34")
            g.shape(rrect(x + 20, -740, 200, 520, 6), "#7a4a2a")
            g.shape(poly([(x + 120, -700), (x + 190, -560), (x + 120, -420), (x + 50, -560)]), "#b8863a", alpha=200)
        c.drawRect(R(self.X0 - 400, -84, self.X1 + 400, 500), g.fill("#6a4a30"))
        g.shape(poly([(-800, -60), (800, -60), (1100, 300), (-1100, 300)]), "#8a1f1a", outline=False)
        g.line([(-800, -60), (800, -60)], color="#d9a93c", w=3)
    def mid(self, g, t):
        x = 420
        g.shape(rrect(x, -420, 260, 340, 6), "#3a1e10")
        g.shape(rrect(x + 16, -404, 228, 300, 4), "#d9a93c")
        for k in range(3):
            g.shape(rrect(x + 30 + k * 72, -390, 60, 270, 3), "#b8863a")
        g.shape(smooth([(x + 120, -470), (x + 110, -520), (x + 130, -560), (x + 150, -520), (x + 140, -470)]), "#d9a93c")
        # tall vase
        g.shape(smooth([(-640, -84), (-670, -180), (-640, -260), (-610, -180)], tension=0.5), "#2f5a7a")


class Ward(Set):
    """hospital ward: white walls, iron beds, ceiling fan"""
    def back(self, g, t):
        c = g.c
        sky(c, self.X0 - 400, -1000, self.X1 + 400, -84, ["#e4e6e0", "#eef0ea", "#d8dad2"])
        c.drawRect(R(self.X0 - 400, -230, self.X1 + 400, -84), g.fill("#b8c8c0"))
        for x in (-800, 400):
            barred_window(g, x, -620, 220, 260, t, bars=3, frame="#8a9a94")
            light_shaft(c, x, x + 220, -360, -180, 120, a=50)
        # ceiling fan
        a = t * 5
        g.line([(0, -1000), (0, -760)], color="#4a4a4a", w=4)
        for k in range(3):
            aa = a + k * 2.09
            g.shape(smooth([(0, -760), (math.cos(aa) * 150, -760 + math.sin(aa) * 10),
                            (math.cos(aa) * 150, -752 + math.sin(aa) * 10)]), "#6a5a4a")
        sky(c, self.X0 - 400, -84, self.X1 + 400, 500, ["#c8c4b4", "#b8b4a4"])
        # far beds
        for x in (-1150, 700):
            self.bed(g, x, -84, t)
    def bed(self, g, x, gy, t):
        c = g.c
        g.line([(x - 110, gy), (x - 110, gy - 90)], color="#8a9a94", w=6)
        g.line([(x + 110, gy), (x + 110, gy - 70)], color="#8a9a94", w=6)
        g.shape(rrect(x - 115, gy - 70, 230, 22, 4), "#f4f4f0")
        g.shape(rrect(x - 108, gy - 84, 50, 18, 8), "#ffffff")
    def mid(self, g, t):
        pass
    def front(self, g, t):
        pass
    def under(self, g, t, x):
        # the bed under the lying patient (drawn before him)
        g.line([(x - 150, 0), (x - 150, -120)], color="#8a9a94", w=7)
        g.line([(x + 40, 0), (x + 40, -90)], color="#8a9a94", w=7)
        g.shape(rrect(x - 160, -76, 215, 26, 4), "#f4f4f0")
        g.shape(rrect(x - 160, -96, 60, 22, 9), "#ffffff")


SETS = dict(village=Village, street=Street, yard=Yard, hut=Hut, temple=Temple, villa=Villa, meyhome=MeyHome,
            prison=Prison, visit=Visit, newhome=NewHome, factory=Factory, hall=Hall, office=Office, clinic=Clinic,
            mansion=Mansion, ward=Ward)

_CACHE = {}
def get_set(loc, tod):
    k = (loc, tod)
    if k not in _CACHE:
        _CACHE[k] = SETS[loc](tod)
    return _CACHE[k]


# ───────────────────────────────────────────────────────────── set dressing (added detail for every location)
def shrine_shelf(g, x, y, t, w=120):
    """household Buddha shelf: red cloth, small gold Buddha, candles, incense smoke."""
    c = g.c
    g.shape(rrect(x - w / 2, y, w, 9, 2), "#6a3f22")
    g.shape(poly([(x - w / 2 + 6, y + 9), (x - w / 2 + 16, y + 26), (x + w / 2 - 16, y + 26), (x + w / 2 - 6, y + 9)]), "#6a3f22")
    c.drawRect(R(x - w / 2 + 2, y - 7, x + w / 2 - 2, y), g.fill("#b3312c"))
    g.shape(smooth([(x - 11, y - 7), (x - 9, y - 28), (x, y - 40), (x + 9, y - 28), (x + 11, y - 7)]), "#d4a93c")
    g.circle(x, y - 40, 4.5, "#d4a93c")
    for k, dx in enumerate((-w * 0.32, w * 0.28)):
        c.drawRect(R(x + dx, y - 22, x + dx + 5, y - 7), g.fill("#f0e6d0"))
        g.ellipse(x + dx + 2.5, y - 26, 2.1, 3.2 + 0.7 * math.sin(t * 9 + k), "#ffcf5a", outline=False)
    for k in range(3):
        pts = [(x + w * 0.12 + 5 * math.sin(t * 0.8 + k + j * 0.6), y - 18 - j * 12 - (t * 9 % 12)) for j in range(6)]
        g.line(pts, color="#d7d2c8", w=1.4, alpha=80)

def basket(g, x, gy, s=1.0, col="#b8904a"):
    b = smooth([(x - 28 * s, gy - 34 * s), (x - 24 * s, gy), (x + 24 * s, gy), (x + 28 * s, gy - 34 * s)], tension=0.3)
    g.shape(b, col)
    for k in range(4):
        g.line([(x - 26 * s, gy - 8 * s - k * 7 * s), (x + 26 * s, gy - 8 * s - k * 7 * s)], color=shade(col, 0.25), w=1.2)

def clothesline(g, x0, x1, y, t, cols=("#e9e2cf", "#2f5d8a", "#b3312c", "#d98f8a")):
    sag = 14
    g.line([(x0, y), ((x0 + x1) / 2, y + sag), (x1, y)], color="#3a2a1a", w=1.5)
    n = len(cols)
    for k, col in enumerate(cols):
        u = (k + 0.7) / (n + 0.4)
        x = x0 + (x1 - x0) * u
        yy = y + sag * (1 - (2 * u - 1) ** 2)
        sw = 2 * math.sin(t * 1.3 + k)
        g.shape(poly([(x - 20, yy), (x + 20, yy), (x + 18 + sw, yy + 56), (x - 18 + sw, yy + 58)]), col)

def water_jar(g, x, gy, s=1.0):
    g.shape(smooth([(x - 22 * s, gy), (x - 34 * s, gy - 40 * s), (x - 20 * s, gy - 74 * s), (x + 20 * s, gy - 74 * s),
                    (x + 34 * s, gy - 40 * s), (x + 22 * s, gy)], tension=0.45), "#8a4a2a")
    g.shape(rrect(x - 22 * s, gy - 82 * s, 44 * s, 10 * s, 3), "#6a3a20")

def rug(g, x0, x1, y0, y1, col="#8a2f28", col2="#d9a93c"):
    r_ = poly([(x0 + 40, y0), (x1 - 40, y0), (x1, y1), (x0, y1)])
    g.shape(r_, col, outline=False)
    inner = poly([(x0 + 60, y0 + 6), (x1 - 60, y0 + 6), (x1 - 24, y1 - 8), (x0 + 24, y1 - 8)])
    g.c.drawPath(inner, g.stroke(col2, 3))
    for k in range(5):
        cx = x0 + (x1 - x0) * (k + 0.5) / 5
        cy = (y0 + y1) / 2
        g.shape(poly([(cx, cy - 10), (cx + 18, cy), (cx, cy + 10), (cx - 18, cy)]), col2, outline=False)

def potted_palm(g, x, gy, t, s=1.0):
    g.shape(poly([(x - 26 * s, gy - 50 * s), (x + 26 * s, gy - 50 * s), (x + 20 * s, gy), (x - 20 * s, gy)]), "#a0522d")
    for k in range(7):
        a = math.radians(-160 + k * 23 + 3 * math.sin(t * 0.8 + k))
        tip = (x + math.cos(a) * 90 * s, gy - 50 * s + math.sin(a) * 110 * s)
        g.shape(smooth([(x, gy - 50 * s), ((x + tip[0]) / 2 - 6, (gy - 50 * s + tip[1]) / 2 - 4), tip,
                        ((x + tip[0]) / 2 + 6, (gy - 50 * s + tip[1]) / 2 + 4)], tension=0.5), mix("#4f7a3e", "#3f6a36", k % 2 * 0.5))

def ceiling_fan(g, x, y, t, s=1.0):
    g.line([(x, y - 200), (x, y)], color="#3a3632", w=4)
    g.circle(x, y, 10 * s, "#5a4a3a")
    a = t * 4
    for k in range(3):
        aa = a + k * 2.09
        g.shape(smooth([(x, y), (x + math.cos(aa) * 130 * s, y + math.sin(aa) * 9 * s),
                        (x + math.cos(aa) * 130 * s, y + 8 * s + math.sin(aa) * 9 * s)]), "#6a4a2e")

def chair(g, x, gy, col="#6a3f22", face=1):
    c = g.c
    c.save(); c.translate(x, gy); c.scale(face, 1)
    g.shape(rrect(-24, -52, 48, 7, 2), col)
    g.line([(-20, -45), (-20, 0)], color=col, w=5); g.line([(20, -45), (20, 0)], color=col, w=5)
    g.line([(-22, -52), (-26, -112)], color=col, w=5)
    for k in range(3):
        g.line([(-25, -64 - k * 16), (-19, -64 - k * 16)], color=col, w=4)
    c.restore()

def monk_bg(g, x, gy, t, s=0.8, walk=0.0):
    """a monk walking with an alms bowl, seen small in the distance (always calm and respectful)."""
    ph = t * 4 * walk
    hh = 160 * s
    sw = math.sin(ph) * 5 * s
    g.limb([(x, gy - hh * 0.4), (x + sw, gy - 3)], hh * 0.07, "#a86d3f")
    g.limb([(x, gy - hh * 0.4), (x - sw, gy - 3)], hh * 0.07, "#a86d3f")
    robe = smooth([(x - hh * 0.13, gy - hh * 0.8), (x + hh * 0.13, gy - hh * 0.8), (x + hh * 0.16, gy - hh * 0.12),
                   (x - hh * 0.16, gy - hh * 0.12)], tension=0.3)
    g.shape(robe, "#e0892a")
    g.line([(x - hh * 0.12, gy - hh * 0.78), (x + hh * 0.1, gy - hh * 0.3)], color="#c9701c", w=2)
    g.ellipse(x + hh * 0.08, gy - hh * 0.52, hh * 0.07, hh * 0.05, "#1c1a18")
    g.circle(x + hh * 0.01, gy - hh * 0.89, hh * 0.085, "#b98253")

def egret(g, x, y, t, s=1.0):
    g.shape(smooth([(x - 14 * s, y), (x, y - 10 * s), (x + 16 * s, y - 4 * s), (x + 2 * s, y + 6 * s)], tension=0.5), "#f4f2ec")
    g.line([(x + 12 * s, y - 6 * s), (x + 16 * s, y - 22 * s), (x + 24 * s, y - 24 * s)], color="#f4f2ec", w=3 * s)
    g.line([(x, y + 4 * s), (x, y + 22 * s)], color="#3a3632", w=1.4)

def medicine_cabinet(g, x, gy):
    g.shape(rrect(x, gy - 240, 150, 240, 3), "#e8e2d4")
    for k in range(3):
        y = gy - 220 + k * 60
        g.line([(x + 8, y + 44), (x + 142, y + 44)], color="#b8b2a4", w=3)
        for j in range(5):
            g.shape(rrect(x + 14 + j * 26, y + 16, 16, 28, 4), ["#6a9ab0", "#a0522d", "#f4f2ec", "#5a7a4a", "#c9a44a"][(j + k) % 5],
                    alpha=220)

def folding_screen(g, x, gy):
    for k in range(3):
        g.shape(rrect(x + k * 62, gy - 190, 58, 190, 2), "#eef0ea")
        g.c.drawRect(R(x + k * 62 + 6, gy - 180, x + k * 62 + 52, gy - 20), g.stroke("#b8c8c0", 2))

def chandelier(g, x, y, t):
    g.line([(x, y - 200), (x, y)], color="#8a6a2a", w=3)
    g.shape(smooth([(x - 60, y), (x - 40, y + 30), (x + 40, y + 30), (x + 60, y)], tension=0.4), "#d4a93c")
    for k in range(5):
        cx = x - 50 + k * 25
        g.line([(cx, y + 30), (cx, y + 48)], color="#d4a93c", w=2)
        g.ellipse(cx, y + 54, 3, 6 + math.sin(t * 8 + k), "#ffdc80", outline=False)
    glow(g.c, x, y + 40, 160, (255, 215, 140), 60)

def _extend(cls, meth, fn):
    orig = getattr(cls, meth)
    def wrapped(self, g, t):
        orig(self, g, t)
        fn(self, g, t)
    setattr(cls, meth, wrapped)

def _village_mid(self, g, t):
    c = g.c
    for k, (x, y) in enumerate(((-420, -40), (220, 30), (820, -70))):
        blob(c, x, y, 260, 22, "#cfe0ea", 90, 4)                   # puddles reflecting the sky
    for k, (x, y) in enumerate(((380, -118), (460, -110), (-980, -122))):
        egret(g, x + 6 * math.sin(t * 0.3 + k), y, t, 1.0)
    for k in range(3):                                              # low morning mist
        blob(c, -900 + k * 800 + 40 * math.sin(t * 0.1 + k), -150, 900, 60, "#fff4e0", 70 if self.tod == "dawn" else 30, 30)
_extend(Village, "mid", _village_mid)

def _hut_mid(self, g, t):
    shrine_shelf(g, -330, -420, t)
    clothesline(g, 480, 900, -560, t)
    basket(g, -900, -84, 1.1)
    basket(g, -836, -84, 0.8, "#a8804a")
    water_jar(g, 780, -84, 0.9)
    g.shape(rrect(-1080, -150, 140, 40, 18), "#c9a867")          # a rolled sleeping mat
_extend(Hut, "mid", _hut_mid)

def _temple_back(self, g, t):
    x = ((t * 18) % 2200) - 1100
    monk_bg(g, x, -150, t, 0.75, walk=1.0)
    for k, x_ in enumerate((620, 660)):                             # incense pot + flower offerings by the steps
        g.shape(rrect(x_ - 16, -118, 32, 22, 5), "#6a6660")
    g.circle(740, -130, 10, "#f4d03a"); g.circle(756, -128, 9, "#e06a8a")
_extend(Temple, "back", _temple_back)

def _villa_mid(self, g, t):
    rug(g, -500, 300, -70, 40)
    potted_palm(g, -860, -84, t, 1.2)
    potted_palm(g, 760, -84, t, 1.0)
    g.shape(rrect(40, -190, 260, 14, 3), "#5a3218")               # dining table and two chairs
    for x in (60, 280):
        g.line([(x, -176), (x, -84)], color="#4a2810", w=7)
    chair(g, 0, -84, face=1); chair(g, 340, -84, face=-1)
    g.shape(rrect(150, -212, 40, 22, 8), "#e8e0d0")                # a covered bowl
_extend(Villa, "mid", _villa_mid)
def _villa_fg(self, g, t):
    ceiling_fan(g, 250, -760, t, 1.0)
_extend(Villa, "fg", _villa_fg)

def _mey_mid(self, g, t):
    shrine_shelf(g, 120, -560, t, 110)
    g.shape(smooth([(820, -84), (812, -150), (870, -170), (930, -150), (922, -84)], tension=0.4), "#d8cba8")  # rice sack
    g.shape(smooth([(-640, -84), (-660, -190), (-620, -230), (-580, -190), (-600, -84)], tension=0.4), "#b8904a")  # fish trap
    for k in range(5):
        g.line([(-652 + k * 4, -100 - k * 25), (-608 - k * 3, -100 - k * 25)], color="#8a6a3a", w=1.4)
_extend(MeyHome, "mid", _mey_mid)

def _prison_mid(self, g, t):
    for k in range(4):                                              # day tallies scratched on the wall
        x0 = -760 + k * 34
        for j in range(4):
            g.line([(x0 + j * 6, -330), (x0 + j * 6, -290)], color="#4a4640", w=2)
        g.line([(x0 - 3, -300), (x0 + 22, -320)], color="#4a4640", w=2)
    g.shape(smooth([(520, -84), (512, -130), (560, -134), (552, -84)], tension=0.3), "#5a5650")   # bucket
    g.shape(rrect(-980, -110, 180, 26, 8), "#6a6e5a")               # folded blanket
_extend(Prison, "mid", _prison_mid)

def _factory_mid(self, g, t):
    people_bg(g, -1200, 1200, -150, 7, t, seed=41, speed=25, h=(135, 150))

def _hall_mid(self, g, t):
    for x in (-900, 700):
        g.shape(rrect(x, -150, 260, 12, 3), "#6b4226")
        for dx in (10, 240):
            g.line([(x + dx, -138), (x + dx, -96)], color="#5a3c24", w=6)
    g.shape(rrect(100, -560, 280, 170, 4), "#2e3a30")                # a blank blackboard
    g.c.drawRect(R(100, -560, 380, -390), g.stroke("#6b4226", 8))
_extend(Hall, "mid", _hall_mid)

def _clinic_mid(self, g, t):
    medicine_cabinet(g, -760, -84)
    chair(g, 560, -84, "#6b4226", face=-1)
_extend(Clinic, "mid", _clinic_mid)

def _ward_mid(self, g, t):
    folding_screen(g, 360, -84)
    g.shape(rrect(170, -150, 60, 66, 3), "#d8d2c4")                 # bedside table + enamel basin & cup
    g.shape(smooth([(172, -150), (180, -166), (220, -166), (228, -150)], tension=0.3), "#f4f4f0")
    g.shape(rrect(210, -176, 12, 14, 3), "#e8e8e4")
_extend(Ward, "mid", _ward_mid)

def _mansion_mid(self, g, t):
    for x in (-900, -700):
        chair(g, x, -84, "#4a2810", face=1)
    potted_palm(g, 880, -84, t, 1.3)
_extend(Mansion, "mid", _mansion_mid)
def _mansion_fg(self, g, t):
    chandelier(g, -100, -760, t)
Mansion.fg = _mansion_fg
