#!/usr/bin/env python3
"""Auto-fix: move/scale elements back into the safe zone.

  autofix.py layout.json [--out fixed.json] [--comfort 20]
  autofix.py fit in.png --preset ig-reel --out out.png [--bg "#000000"]   (shrink whole frame into safe area)
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zones_lib as Z


def fix_element(el, safe, avoids, pad=16):
    el, notes = dict(el), []
    sx, sy, sw, sh = safe
    if el["w"] > sw or el["h"] > sh:
        k = min(sw / el["w"], sh / el["h"])
        el["w"], el["h"] = round(el["w"] * k), round(el["h"] * k)
        if "size" in el:
            el["size"] = round(el["size"] * k)
        notes.append(f"scaled x{k:.2f}")
    nx = min(max(el["x"], sx), sx + sw - el["w"])
    ny = min(max(el["y"], sy), sy + sh - el["h"])
    if (nx, ny) != (el["x"], el["y"]):
        notes.append(f"moved ({el['x']},{el['y']}) -> ({nx},{ny})")
    el["x"], el["y"] = nx, ny
    for label, r in avoids:
        box = (el["x"], el["y"], el["w"], el["h"])
        if not Z.overlaps(box, r):
            continue
        cands = []  # (cost, x, y, scale)
        for cx, cy in ((el["x"], r[1] - el["h"] - pad), (r[0] - el["w"] - pad, el["y"])):
            cands.append((abs(cx - el["x"]) + abs(cy - el["y"]), cx, cy, 1.0))
        if "size" in el:  # text can also shrink to stay left of the zone
            k = (r[0] - pad - el["x"]) / el["w"]
            if 0.75 <= k < 1:
                cands.append(((1 - k) * 500, el["x"], el["y"], k))
        for cost, cx, cy, k in sorted(cands):
            cand = (cx, cy, el["w"] * k, el["h"] * k)
            if Z.inside(cand, safe) and not any(Z.overlaps(cand, rr) for _, rr in avoids):
                el["x"], el["y"] = cx, cy
                if k != 1.0:
                    el["w"], el["h"], el["size"] = round(el["w"] * k), round(el["h"] * k), round(el["size"] * k)
                    notes.append(f"scaled x{k:.2f} to clear '{label}'")
                else:
                    notes.append(f"moved clear of '{label}'")
                break
        else:
            notes.append(f"UNFIXABLE: still touches '{label}', shorten or resize it")
    return el, notes


def cmd_layout(a):
    layout = json.load(open(a.input))
    p = Z.preset(a.preset or layout["preset"], a.zones)
    safe, avoids = Z.safe_rect(p, a.comfort), Z.avoid_rects(p)
    out, changed = [], 0
    for el in layout["elements"]:
        if el.get("important", True) is False:
            out.append(el)
            continue
        new, notes = fix_element(el, safe, avoids)
        if notes:
            changed += 1
            print(f"- {el.get('id', el.get('type'))}: " + "; ".join(notes))
        out.append(new)
    layout["elements"] = out
    dest = a.out or os.path.splitext(a.input)[0] + ".fixed.json"
    json.dump(layout, open(dest, "w"), indent=2)
    print(f"{changed} element(s) fixed -> {dest}")


def cmd_fit(a):
    from PIL import Image
    p = Z.preset(a.preset, a.zones)
    sx, sy, sw, sh = Z.safe_rect(p, a.comfort)
    im = Image.open(a.input).convert("RGB")
    k = min(sw / im.width, sh / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)))
    canvas = Image.new("RGB", (p["width"], p["height"]), a.bg)
    canvas.paste(im, (sx + (sw - im.width) // 2, sy + (sh - im.height) // 2))
    canvas.save(a.out)
    print(f"saved {a.out} (content scaled x{k:.2f} into safe area)")
    print(f'ffmpeg equivalent for video: -vf "scale={sw}:{sh}:force_original_aspect_ratio=decrease,'
          f'pad={p["width"]}:{p["height"]}:(ow-iw)/2:(oh-ih)/2:color=black"')


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("second", nargs="?")
    ap.add_argument("--preset"); ap.add_argument("--zones"); ap.add_argument("--out")
    ap.add_argument("--comfort", type=int, default=0); ap.add_argument("--bg", default="#000000")
    a = ap.parse_args()
    if a.input == "fit":
        a.input = a.second
        cmd_fit(a)
    else:
        cmd_layout(a)
