"""Shared helpers. Everything reads zones.json, nothing is hard-coded."""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ZONES = os.path.normpath(os.path.join(HERE, "..", "zones.json"))


def load(path=None):
    with open(path or DEFAULT_ZONES, encoding="utf-8") as f:
        return json.load(f)


def preset(name, path=None):
    presets = load(path)["presets"]
    if name not in presets:
        sys.exit(f"Unknown preset '{name}'. Available: {', '.join(presets)}")
    p = dict(presets[name])
    p["name"] = name
    return p


def safe_rect(p, comfort=0):
    s = p["safe"]
    return (s["left"] + comfort, s["top"] + comfort,
            p["width"] - s["left"] - s["right"] - 2 * comfort,
            p["height"] - s["top"] - s["bottom"] - 2 * comfort)


def avoid_rects(p):
    return [(a["label"], (a["x"], a["y"], a["w"], a["h"])) for a in p.get("avoid", [])]


def forbidden_rects(p, comfort=0):
    """Bands outside the safe rect + extra avoid rectangles."""
    W, H = p["width"], p["height"]
    sx, sy, sw, sh = safe_rect(p, comfort)
    out = [("top margin", (0, 0, W, sy)), ("bottom margin", (0, sy + sh, W, H - sy - sh)),
           ("left margin", (0, 0, sx, H)), ("right margin", (sx + sw, 0, W - sx - sw, H))]
    out = [(l, r) for l, r in out if r[2] > 0 and r[3] > 0]
    return out + avoid_rects(p)


def overlaps(a, b, tol=1):
    return not (a[0] + a[2] <= b[0] + tol or b[0] + b[2] <= a[0] + tol or
                a[1] + a[3] <= b[1] + tol or b[1] + b[3] <= a[1] + tol)


def inside(a, r, tol=1):
    return (a[0] >= r[0] - tol and a[1] >= r[1] - tol and
            a[0] + a[2] <= r[0] + r[2] + tol and a[1] + a[3] <= r[1] + r[3] + tol)


def grid_rect(p):
    g = p.get("grid")
    if not g:
        return None
    return ((p["width"] - g["width"]) // 2, (p["height"] - g["height"]) // 2, g["width"], g["height"])


def get_font(size, bold=True):
    from PIL import ImageFont
    names = ["DejaVuSans-Bold.ttf", "DejaVuSans.ttf"] if bold else ["DejaVuSans.ttf"]
    for base in ("/usr/share/fonts/truetype/dejavu/", "/Library/Fonts/", "C:/Windows/Fonts/", ""):
        for n in names + ["Arial Bold.ttf", "arialbd.ttf", "Arial.ttf"]:
            try:
                return ImageFont.truetype(os.path.join(base, n), size)
            except Exception:
                continue
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def draw_overlay(img, p, violations=None, comfort=0):
    """Red = keep clear, green = safe area, cyan = grid crop, yellow = violations."""
    from PIL import Image, ImageDraw
    base = img.convert("RGBA")
    W, H = base.size
    kx, ky = W / p["width"], H / p["height"]
    sc = lambda r: (r[0] * kx, r[1] * ky, (r[0] + r[2]) * kx, (r[1] + r[3]) * ky)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = get_font(max(12, int(H * 0.016)))
    for label, r in forbidden_rects(p, comfort):
        d.rectangle(sc(r), fill=(255, 40, 70, 85))
        d.text((sc(r)[0] + 6, sc(r)[1] + 4), "AVOID", font=f, fill=(255, 255, 255, 230))
    d.rectangle(sc(safe_rect(p, comfort)), outline=(40, 230, 120, 255), width=max(2, int(W * 0.004)))
    g = grid_rect(p)
    if g:
        d.rectangle(sc(g), outline=(0, 200, 255, 255), width=max(2, int(W * 0.003)))
        d.text((sc(g)[0] + 6, sc(g)[3] - 24), "GRID", font=f, fill=(0, 200, 255, 255))
    for v in violations or []:
        d.rectangle(sc(v["bbox"]), outline=(255, 230, 0, 255), width=max(3, int(W * 0.005)))
    return Image.alpha_composite(base, layer)


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "list":
        for k, v in load()["presets"].items():
            print(f"{k:16} {v['width']}x{v['height']}  {v['label']}")
    elif len(sys.argv) >= 3 and sys.argv[1] == "show":
        p = preset(sys.argv[2])
        x, y, w, h = safe_rect(p)
        print(f"{p['label']}  {p['width']}x{p['height']}")
        print(f"SAFE AREA  x={x} y={y} w={w} h={h}   (x {x}..{x+w}, y {y}..{y+h})")
        for l, r in avoid_rects(p):
            print(f"AVOID      {l}: x={r[0]} y={r[1]} w={r[2]} h={r[3]}")
        if p.get("grid"):
            print("GRID CROP ", grid_rect(p))
    else:
        print("usage: zones_lib.py list | show <preset>")
