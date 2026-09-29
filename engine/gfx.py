# Small skia drawing helpers shared by the character rig and the sets.
import math
import skia

def rgb(h, a=255):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)

def mix(h1, h2, t):
    a = [int(h1.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    b = [int(h2.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    return "#%02x%02x%02x" % tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))

def shade(h, t=0.22):
    return mix(h, "#2a1408", t)

def light(h, t=0.25):
    return mix(h, "#fff4e0", t)

OUTLINE = "#3a2217"

class Ctx:
    """Holds the canvas and the current screen-space zoom so outlines stay a sane pixel width."""
    def __init__(self, canvas, zoom=1.0):
        self.c = canvas
        self.zoom = zoom

    def lw(self, px=2.2, lo=1.1, hi=4.2):
        # outline width in local units that renders ~px screen pixels, clamped
        z = max(self.zoom, 1e-3)
        w = min(max(px * (z / 6.0) ** 0.45, lo), hi)
        return w / z

    def fill(self, color, alpha=255):
        p = skia.Paint(AntiAlias=True, Color=rgb(color, alpha) if isinstance(color, str) else color)
        p.setStyle(skia.Paint.kFill_Style)
        return p

    def stroke(self, color, w, alpha=255, cap=skia.Paint.kRound_Cap):
        p = skia.Paint(AntiAlias=True, Color=rgb(color, alpha) if isinstance(color, str) else color)
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(w)
        p.setStrokeCap(cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
        return p

    def shape(self, path, color, outline=True, alpha=255, olw=None):
        self.c.drawPath(path, self.fill(color, alpha))
        if outline:
            self.c.drawPath(path, self.stroke(OUTLINE, olw or self.lw(), alpha))

    def limb(self, pts, width, color, outline=True, alpha=255, cap=skia.Paint.kRound_Cap):
        """A thick rounded polyline with an outline (double stroke)."""
        path = poly(pts, close=False)
        if outline:
            self.c.drawPath(path, self.stroke(OUTLINE, width + 2 * self.lw(), alpha, cap=cap))
        self.c.drawPath(path, self.stroke(color, width, alpha, cap=cap))

    def line(self, pts, color=OUTLINE, w=None, alpha=255):
        self.c.drawPath(poly(pts, close=False), self.stroke(color, w or self.lw(), alpha))

    def circle(self, x, y, r, color, outline=True, alpha=255):
        self.c.drawCircle(x, y, r, self.fill(color, alpha))
        if outline:
            self.c.drawCircle(x, y, r, self.stroke(OUTLINE, self.lw(), alpha))

    def ellipse(self, x, y, rx, ry, color, outline=True, alpha=255, rot=0):
        c = self.c
        c.save()
        c.translate(x, y)
        if rot:
            c.rotate(rot)
        r = skia.Rect.MakeLTRB(-rx, -ry, rx, ry)
        c.drawOval(r, self.fill(color, alpha))
        if outline:
            c.drawOval(r, self.stroke(OUTLINE, self.lw(), alpha))
        c.restore()


def poly(pts, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p

def smooth(pts, close=True, tension=0.5):
    """Catmull-Rom through points -> cubic path."""
    p = skia.Path()
    n = len(pts)
    if n < 3:
        return poly(pts, close)
    p.moveTo(*pts[0])
    rng = range(n) if close else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if (close or i > 0) else pts[0]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (close or i + 2 < n) else pts[-1]
        t = tension / 3.0 * 2
        c1 = (p1[0] + (p2[0] - p0[0]) * t / 2, p1[1] + (p2[1] - p0[1]) * t / 2)
        c2 = (p2[0] - (p3[0] - p1[0]) * t / 2, p2[1] - (p3[1] - p1[1]) * t / 2)
        p.cubicTo(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if close:
        p.close()
    return p

def rrect(x, y, w, h, r):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r))
    return p

def lin_grad(p0, p1, colors, pos=None):
    return skia.GradientShader.MakeLinear([skia.Point(*p0), skia.Point(*p1)],
                                          [rgb(c) if isinstance(c, str) else c for c in colors], pos)

def rad_grad(center, r, colors, pos=None):
    return skia.GradientShader.MakeRadial(skia.Point(*center), r,
                                          [rgb(c) if isinstance(c, str) else c for c in colors], pos)

def ang(a):
    return math.radians(a)

def rot_pt(x, y, a):
    ca, sa = math.cos(a), math.sin(a)
    return (x * ca - y * sa, x * sa + y * ca)

def lerp(a, b, t):
    return a + (b - a) * t

def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)
