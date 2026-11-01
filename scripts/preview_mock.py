#!/usr/bin/env python3
"""Fake app preview: your frame inside a mock Instagram / TikTok / Shorts / LinkedIn UI.

  preview_mock.py frame.png --preset ig-reel --out mock.png [--user @name] [--caption "text"]
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zones_lib as Z
from PIL import Image, ImageDraw

WHITE, SOFT = (255, 255, 255, 255), (255, 255, 255, 150)


def side_rail(d, p, labels, x_center, y_bottom):
    f = Z.get_font(30, bold=False)
    y = y_bottom
    for lab in reversed(labels):
        d.ellipse((x_center - 36, y - 72, x_center + 36, y), fill=(0, 0, 0, 110), outline=WHITE, width=3)
        w = d.textlength(lab, font=f)
        d.text((x_center - w / 2, y + 8), lab, font=f, fill=WHITE)
        y -= 150


def caption_block(d, p, user, caption, y):
    d.ellipse((40, y, 100, y + 60), fill=(120, 120, 120, 255), outline=WHITE, width=3)
    d.text((118, y + 10), user, font=Z.get_font(36), fill=WHITE)
    d.text((40, y + 90), caption, font=Z.get_font(34, bold=False), fill=WHITE)
    d.rectangle((40, y + 150, 640, y + 168), fill=SOFT)


def vertical_ui(img, p, a):
    W, H = img.size
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ui = p["ui"]
    if ui == "story":
        for i in range(3):
            d.rounded_rectangle((30 + i * 340, 36, 350 + i * 340, 44), 4, fill=WHITE if i == 0 else SOFT)
        d.ellipse((30, 70, 100, 140), fill=(120, 120, 120, 255), outline=WHITE, width=3)
        d.text((116, 88), a.user, font=Z.get_font(36), fill=WHITE)
        d.rounded_rectangle((40, H - 150, W - 160, H - 70), 40, outline=WHITE, width=3)
        d.text((80, H - 130), "Send message", font=Z.get_font(34, bold=False), fill=WHITE)
        d.ellipse((W - 140, H - 150, W - 60, H - 70), outline=WHITE, width=3)
    else:
        title = {"reel": "Reels", "tiktok": "Following   For You"}.get(ui, "Shorts")
        d.text((40, 80), title, font=Z.get_font(50), fill=WHITE)
        side_rail(d, p, ["12K", "340", "Share", "Save"][: 4], W - 90, H - 560 if ui != "reel" else H - 380)
        caption_block(d, p, a.user, a.caption, H - 330 if ui == "reel" else H - 470)
    return Image.alpha_composite(img, layer)


def feed_ui(img, p, a):
    W, H = img.size
    top, bottom = 120, 110
    canvas = Image.new("RGBA", (W, H + top + bottom), (255, 255, 255, 255))
    canvas.paste(img, (0, top))
    d = ImageDraw.Draw(canvas)
    d.ellipse((24, 24, 96, 96), fill=(200, 200, 200, 255))
    d.text((114, 42), a.user, font=Z.get_font(max(28, W // 30)), fill=(20, 20, 20, 255))
    for i in range(3):
        d.ellipse((24 + i * 90, H + top + 28, 84 + i * 90, H + top + 88), outline=(20, 20, 20, 255), width=4)
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input"); ap.add_argument("--preset", required=True)
    ap.add_argument("--out", default="mock.png"); ap.add_argument("--zones")
    ap.add_argument("--user", default="@yourhandle"); ap.add_argument("--caption", default="Your caption goes here #safezone")
    a = ap.parse_args()
    p = Z.preset(a.preset, a.zones)
    img = Image.open(a.input).convert("RGBA").resize((p["width"], p["height"]))
    out = feed_ui(img, p, a) if p["ui"] == "feed" else vertical_ui(img, p, a)
    out.convert("RGB").save(a.out)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
