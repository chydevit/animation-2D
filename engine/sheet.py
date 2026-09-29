# Character reference sheets (lineup, per-character pose/expression/mouth sheets).
import os, sys, math
import skia
from gfx import rgb, Ctx
from chars import Rig, CAST, POSES, EXPR, MOUTHS, blend_pose

HERE = os.path.dirname(os.path.abspath(__file__))
import config
OUT = config.ep("characters")
os.makedirs(OUT, exist_ok=True)

def surface(w, h, bg="#f7f1e6"):
    s = skia.Surface(w, h)
    c = s.getCanvas()
    c.clear(rgb(bg))
    return s, c

def st(pose="stand", expr="neutral", facing=1, mouth=(None, 0), look=(0.35, 0), t=0.0, blink=0.0):
    return dict(pose=dict(POSES[pose]), expr=EXPR[expr], facing=facing, mouth=mouth, look=look, t=t, blink=blink)

def draw_char(c, name, x, y, zoom, **kw):
    c.save(); c.translate(x, y); c.scale(zoom, zoom)
    Rig(name).draw(c, zoom, 0, 0, st(**kw))
    c.restore()

def save(s, name):
    img = s.makeImageSnapshot()
    p = os.path.join(OUT, name)
    img.save(p, skia.kPNG)
    print("wrote", p)

def lineup():
    names = list(CAST)
    W, H = 150 + len(names) * 200, 1000
    s, c = surface(W, H)
    z = 4.6
    for i, n in enumerate(names):
        draw_char(c, n, 120 + i * 200, 900, z)
    save(s, "00_lineup.png")

def head_at(c, name, cx, cy, zoom, **kw):
    r = Rig(name)
    s = st(**kw)
    J = r.skeleton(s["pose"])
    hx, hy = J["head"]
    c.save(); c.translate(cx, cy); c.scale(zoom, zoom); c.translate(-hx, -hy)
    rr = r.s["head_r"]
    c.clipRect(skia.Rect.MakeLTRB(hx - rr * 1.6, hy - rr * 1.5, hx + rr * 1.7, hy + rr * 1.5))
    r.draw(c, zoom, 0, 0, s)
    c.restore()

def char_sheet(name):
    from gfx import rrect
    W, H = 2600, 1500
    s, c = surface(W, H)
    # panel backgrounds
    for (x, y, w, h) in ((30, 30, 820, 1000), (880, 30, 1690, 1000), (30, 1060, 1580, 410), (1640, 1060, 930, 410)):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), 18, 18), skia.Paint(Color=rgb("#fffaf1")))
    ch_h = CAST[name]["H"]
    z = 820 / ch_h
    draw_char(c, name, 230, 960, z * 1.05)
    draw_char(c, name, 620, 960, z * 1.05, facing=-1)
    poses = ["point", "sampeah", "hand_chest", "shock", "arms_crossed", "sit", "kneel", "carry"]
    for i, p in enumerate(poses):
        draw_char(c, name, 990 + i * 205, 960, z * 0.72, pose=p, expr="neutral" if p != "shock" else "shock")
    ex = ["neutral", "happy", "worried", "sad", "angry", "shock", "serious", "tired", "smug", "cry"]
    for i, e in enumerate(ex):
        head_at(c, name, 110 + i * 152, 1265, 4.3, expr=e)
    for i, m in enumerate(["closed", "A", "E", "I", "O", "U", "small", "wide", "smile", "surprisedO"]):
        head_at(c, name, 1720 + (i % 5) * 180, 1170 + (i // 5) * 190, 3.4, mouth=(m, 1.0))
    save(s, f"{name}_sheet.png")

if __name__ == "__main__":
    what = sys.argv[1:] or ["lineup"]
    for w in what:
        if w == "lineup":
            lineup()
        elif w == "all":
            lineup()
            for n in CAST:
                char_sheet(n)
        else:
            char_sheet(w)
