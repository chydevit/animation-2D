# Title card + chapter cards as transparent PNGs (Khmer shaped with libraqm).
# Run with ~/voxcpm-env/bin/python (its Pillow has raqm).
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, features

import config
OUT = config.ep("characters", "cards")
os.makedirs(OUT, exist_ok=True)
assert features.check("raqm"), "Pillow without raqm cannot shape Khmer"
KH = "/System/Library/Fonts/Supplemental/Khmer MN.ttc"
KH2 = "/System/Library/Fonts/Supplemental/Khmer Sangam MN.ttf"
EN = "/System/Library/Fonts/Supplemental/Georgia.ttf"
if not os.path.exists(EN):
    EN = "/System/Library/Fonts/Helvetica.ttc"

def font(p, size, index=0):
    return ImageFont.truetype(p, size, index=index, layout_engine=ImageFont.Layout.RAQM)

def text_img(lines, pad=40, shadow=True):
    """lines: [(text, font, fill, lang)] stacked and centred."""
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    boxes = [d.textbbox((0, 0), tx, font=f, language=lang) for (tx, f, col, lang) in lines]
    w = max(b[2] - b[0] for b in boxes) + pad * 2
    gap = 18
    h = sum(b[3] - b[1] for b in boxes) + gap * (len(lines) - 1) + pad * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d, ds = ImageDraw.Draw(img), ImageDraw.Draw(sh)
    y = pad
    for (tx, f, col, lang), b in zip(lines, boxes):
        x = (w - (b[2] - b[0])) / 2 - b[0]
        ds.text((x + 3, y - b[1] + 4), tx, font=f, fill=(20, 10, 4, 200), language=lang)
        d.text((x, y - b[1]), tx, font=f, fill=col, language=lang)
        y += b[3] - b[1] + gap
    if shadow:
        sh = sh.filter(ImageFilter.GaussianBlur(6))
        sh.alpha_composite(img)
        return sh
    return img

def title():
    img = text_img([
        (config.P.TITLE_KH, font(KH, 104, 1), (255, 236, 190, 255), "km"),
        (config.P.TITLE_EN, font(EN, 40), (255, 244, 225, 235), "en"),
        (getattr(config.P, "CREDIT_KH", ""), font(KH2, 34), (255, 240, 215, 220), "km"),
    ], pad=60)
    img.save(os.path.join(OUT, "title.png"))

KH_NUM = "០១២៣៤៥៦៧៨៩"
def kn(n):
    return "".join(KH_NUM[int(ch)] for ch in str(n))

CHAPTERS = config.P.CHAPTERS

def chapters():
    for n, (kh, en) in CHAPTERS.items():
        img = text_img([
            (f"ជំពូកទី {kn(n)}", font(KH2, 30), (255, 226, 170, 235), "km"),
            (kh, font(KH, 54, 1), (255, 248, 232, 255), "km"),
            (en, font(EN, 26), (240, 232, 215, 220), "en"),
        ], pad=28)
        # soft dark plate behind for readability
        plate = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(plate).rounded_rectangle((6, 6, img.size[0] - 6, img.size[1] - 6), 22, fill=(18, 10, 6, 120))
        plate.alpha_composite(img)
        plate.save(os.path.join(OUT, f"ch{n:02d}.png"))

if __name__ == "__main__":
    title(); chapters()
    print("cards ->", os.path.abspath(OUT))
