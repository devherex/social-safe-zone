#!/usr/bin/env python3
"""Pass/fail safe-zone check for a layout JSON, an image, or a video.

  check_zones.py layout.json                         exact check (best)
  check_zones.py frame.png --preset ig-reel          pixel check (OCR if installed)
  check_zones.py reel.mp4  --preset ig-reel --every 1
Options: --overlay out.png  --json report.json  --comfort 20  --ocr  --zones custom.json
Exit code 0 = PASS, 1 = FAIL.
"""
import argparse, json, os, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zones_lib as Z
from PIL import Image, ImageFilter

EDGE_T, RATIO_T = 40, 0.012


def check_layout(layout, p, comfort):
    viol = []
    forb = Z.forbidden_rects(p, comfort)
    for el in layout["elements"]:
        if el.get("important", True) is False:
            continue
        box = (el["x"], el["y"], el["w"], el["h"])
        for label, r in forb:
            if Z.overlaps(box, r):
                viol.append({"what": el.get("id", el.get("type", "element")), "zone": label, "bbox": box})
                break
    return viol


def ocr_boxes(img):
    try:
        import pytesseract
    except ImportError:
        return None
    d = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    return [(d["left"][i], d["top"][i], d["width"][i], d["height"][i], d["text"][i])
            for i in range(len(d["text"])) if d["text"][i].strip() and float(d["conf"][i]) > 50]


def check_image(img, p, comfort, use_ocr):
    W, H = p["width"], p["height"]
    img = img.convert("RGB").resize((W, H))
    forb = Z.forbidden_rects(p, comfort)
    viol = []
    boxes = ocr_boxes(img) if use_ocr else None
    if boxes is not None:
        for (x, y, w, h, t) in boxes:
            for label, r in forb:
                if Z.overlaps((x, y, w, h), r):
                    viol.append({"what": f"text '{t}'", "zone": label, "bbox": (x, y, w, h)})
                    break
        return viol, "ocr"
    edges = img.convert("L").filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > EDGE_T else 0)
    for label, (x, y, w, h) in forb:
        crop = edges.crop((x, y, x + w, y + h))
        ratio = crop.histogram()[255] / max(1, w * h)
        bb = crop.getbbox()
        if ratio > RATIO_T and bb:
            viol.append({"what": f"content ({ratio:.1%} edge pixels)", "zone": label,
                         "bbox": (x + bb[0], y + bb[1], bb[2] - bb[0], bb[3] - bb[1])})
    return viol, "pixels"


def extract_frames(path, p, every, tmp):
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found. Install it to check videos.")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-vf",
                    f"fps=1/{every},scale={p['width']}:{p['height']}", "-q:v", "3",
                    os.path.join(tmp, "f_%04d.png")], check=True)
    return sorted(os.path.join(tmp, f) for f in os.listdir(tmp) if f.startswith("f_"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--preset")
    ap.add_argument("--zones")
    ap.add_argument("--every", type=float, default=1.0, help="video: seconds between sampled frames")
    ap.add_argument("--comfort", type=int, default=0, help="extra inner padding in px")
    ap.add_argument("--ocr", action="store_true", help="use pytesseract to find text boxes")
    ap.add_argument("--overlay")
    ap.add_argument("--json")
    a = ap.parse_args()

    ext = os.path.splitext(a.input)[1].lower()
    report = {"input": a.input, "frames": []}
    worst = None

    if ext == ".json":
        layout = json.load(open(a.input))
        p = Z.preset(a.preset or layout["preset"], a.zones)
        viol = check_layout(layout, p, a.comfort)
        frames = [("layout", viol)]
        method = "layout"
        base_img = Image.new("RGB", (p["width"], p["height"]), (20, 20, 20))
        worst_img = base_img
    else:
        if not a.preset:
            sys.exit("--preset is required for images and videos (see: zones_lib.py list)")
        p = Z.preset(a.preset, a.zones)
        frames, method, worst_img = [], "pixels", None
        if ext in (".mp4", ".mov", ".webm", ".mkv", ".m4v"):
            tmp = tempfile.mkdtemp()
            paths = extract_frames(a.input, p, a.every, tmp)
            labels = [f"{i * a.every:.1f}s" for i in range(len(paths))]
        else:
            paths, labels = [a.input], ["image"]
        for path, lab in zip(paths, labels):
            im = Image.open(path)
            if abs(im.width / im.height - p["width"] / p["height"]) > 0.02:
                print(f"! warning: aspect {im.width}x{im.height} differs from preset {p['width']}x{p['height']}")
            v, method = check_image(im, p, a.comfort, a.ocr)
            frames.append((lab, v))
            if worst is None or len(v) > len(worst[1]):
                worst = (lab, v)
                worst_img = im.convert("RGB").resize((p["width"], p["height"]))

    total = len(frames)
    bad = [f for f in frames if f[1]]
    score = round(100 * (total - len(bad)) / total) if total else 100
    status = "PASS" if not bad else "FAIL"
    print(f"{status}  score {score}/100   preset: {p['name']}   method: {method}")
    if method == "pixels":
        print("  (pixel mode is a heuristic; use --ocr for text, or a layout JSON for exact results)")
    for lab, v in bad[:12]:
        for x in v:
            bb = tuple(int(n) for n in x["bbox"])
            print(f"  x {lab}: {x['what']} touches {x['zone']}  at {bb}")
    if len(bad) > 12:
        print(f"  ... and {len(bad) - 12} more frames")
    if a.overlay:
        worst_v = max(frames, key=lambda f: len(f[1]))[1]
        Z.draw_overlay(worst_img, p, worst_v, a.comfort).convert("RGB").save(a.overlay)
        print(f"overlay saved: {a.overlay}")
    if a.json:
        report.update(status=status, score=score, preset=p["name"], method=method,
                      frames=[{"at": l, "violations": v} for l, v in frames])
        json.dump(report, open(a.json, "w"), indent=2)
    sys.exit(0 if status == "PASS" else 1)


if __name__ == "__main__":
    main()
