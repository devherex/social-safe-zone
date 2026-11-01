#!/usr/bin/env python3
"""Make transparent guide PNGs (drop on top of any design) or overlay one on a frame.

  make_guides.py --all [--out assets/guides]
  make_guides.py --preset ig-reel --on frame.png --out frame_guides.png
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zones_lib as Z
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("--all", action="store_true"); ap.add_argument("--preset")
ap.add_argument("--on"); ap.add_argument("--out", default="guide.png")
ap.add_argument("--zones"); ap.add_argument("--comfort", type=int, default=0)
a = ap.parse_args()

if a.all:
    os.makedirs(a.out if a.out != "guide.png" else "assets/guides", exist_ok=True)
    folder = a.out if a.out != "guide.png" else "assets/guides"
    for name in Z.load(a.zones)["presets"]:
        p = Z.preset(name, a.zones)
        g = Z.draw_overlay(Image.new("RGBA", (p["width"], p["height"]), (0, 0, 0, 0)), p, comfort=a.comfort)
        g.save(os.path.join(folder, f"{name}.png"))
        print("wrote", os.path.join(folder, f"{name}.png"))
else:
    if not a.preset:
        sys.exit("use --all or --preset NAME")
    p = Z.preset(a.preset, a.zones)
    base = Image.open(a.on).convert("RGBA").resize((p["width"], p["height"])) if a.on \
        else Image.new("RGBA", (p["width"], p["height"]), (0, 0, 0, 0))
    Z.draw_overlay(base, p, comfort=a.comfort).save(a.out)
    print("wrote", a.out)
