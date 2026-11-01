#!/usr/bin/env python3
"""Render a layout JSON to a PNG (text, boxes, logos as labelled boxes). Handy for quick checks.

  render_layout.py layout.json out.png [--bg "#0b0b0f"]
Element: {"id","type":"text|box","x","y","w","h","text","size","color"}
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zones_lib as Z
from PIL import Image, ImageDraw


def render(layout, bg="#0b0b0f", zones=None):
    p = Z.preset(layout["preset"], zones)
    img = Image.new("RGB", (p["width"], p["height"]), bg)
    d = ImageDraw.Draw(img)
    for el in layout["elements"]:
        box = (el["x"], el["y"], el["x"] + el["w"], el["y"] + el["h"])
        if el["type"] == "text":
            d.text((el["x"], el["y"]), el["text"], font=Z.get_font(el.get("size", 60)), fill=el.get("color", "#ffffff"))
        else:
            d.rounded_rectangle(box, 24, fill=el.get("color", "#38bdf8"))
            if el.get("text"):
                d.text((el["x"] + 24, el["y"] + el["h"] // 2 - 20), el["text"], font=Z.get_font(el.get("size", 40)), fill="#000000")
    return img


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("layout"); ap.add_argument("out"); ap.add_argument("--bg", default="#0b0b0f")
    a = ap.parse_args()
    render(json.load(open(a.layout)), a.bg).save(a.out)
    print("wrote", a.out)
