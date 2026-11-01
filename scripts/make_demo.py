#!/usr/bin/env python3
"""Builds the before/after demo images + GIF used in the README."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zones_lib as Z
from render_layout import render
from autofix import fix_element
from check_zones import check_layout
from PIL import Image, ImageDraw
import subprocess

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
EX, AS = os.path.join(ROOT, "examples"), os.path.join(ROOT, "assets")
os.makedirs(EX, exist_ok=True)

def text_el(id, text, x, y, size, color="#ffffff"):
    f = Z.get_font(size)
    l, t, r, b = f.getbbox(text)
    return {"id": id, "type": "text", "text": text, "x": x, "y": y, "w": r - l, "h": b - t + 8, "size": size, "color": color}

bad = {"preset": "ig-reel", "elements": [
    text_el("headline", "STOP LOSING VIEWS", 60, 70, 96, "#38bdf8"),
    text_el("subtitle", "Keep text inside the safe zone", 60, 1790, 56),
    {"id": "cta-button", "type": "box", "text": "Book now", "x": 800, "y": 1260, "w": 250, "h": 110, "size": 40, "color": "#38bdf8"},
    {"id": "logo", "type": "box", "text": "LOGO", "x": 40, "y": 1500, "w": 220, "h": 110, "size": 40, "color": "#94a3b8"},
]}
json.dump(bad, open(os.path.join(EX, "bad_layout.json"), "w"), indent=2)

p = Z.preset("ig-reel")
fixed = dict(bad)
fixed["elements"] = [fix_element(e, Z.safe_rect(p), Z.avoid_rects(p))[0] for e in bad["elements"]]
json.dump(fixed, open(os.path.join(EX, "bad_layout.fixed.json"), "w"), indent=2)

print("before:", len(check_layout(bad, p, 0)), "violations | after:", len(check_layout(fixed, p, 0)))

bg = lambda: "#0b0b0f"
b_img, a_img = render(bad, bg()), render(fixed, bg())
b_img.save(os.path.join(EX, "before.png")); a_img.save(os.path.join(EX, "after.png"))
b_g = Z.draw_overlay(b_img, p, check_layout(bad, p, 0)).convert("RGB")
a_g = Z.draw_overlay(a_img, p, []).convert("RGB")
b_g.save(os.path.join(EX, "before_guides.png")); a_g.save(os.path.join(EX, "after_guides.png"))
for n, src in (("before", "before.png"), ("after", "after.png")):
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "preview_mock.py"), os.path.join(EX, src),
                    "--preset", "ig-reel", "--out", os.path.join(EX, f"{n}_mock.png")], check=True, capture_output=True)

def tile(path, label):
    im = Image.open(path).convert("RGB").resize((360, 640))
    c = Image.new("RGB", (360, 700), "#0b0b0f"); c.paste(im, (0, 60))
    ImageDraw.Draw(c).text((16, 14), label, font=Z.get_font(30), fill="#38bdf8")
    return c

def pair(l, r):
    c = Image.new("RGB", (740, 700), "#0b0b0f"); c.paste(l, (0, 0)); c.paste(r, (380, 0)); return c

frames = [
    pair(tile(os.path.join(EX, "before_guides.png"), "BEFORE (zones)"), tile(os.path.join(EX, "after_guides.png"), "AFTER (auto-fix)")),
    pair(tile(os.path.join(EX, "before_mock.png"), "BEFORE (in app)"), tile(os.path.join(EX, "after_mock.png"), "AFTER (in app)")),
]
frames[0].save(os.path.join(AS, "demo.gif"), save_all=True, append_images=frames[1:], duration=2200, loop=0)
frames[0].save(os.path.join(AS, "demo.png"))
print("demo written")
