# Using the safe zones in any tool

## Remotion
```bash
cp templates/SafeZone.tsx templates/zones.ts src/
```
```tsx
<SafeZone preset="ig-reel" debug>   {/* remove debug before render */}
  <h1>Headline</h1>
</SafeZone>
```
Set the composition to the preset size (for example 1080x1920).

## HTML / CSS / web tools
```html
<link rel="stylesheet" href="templates/safezone.css">
<div class="frame sz-ig-reel debug"><div class="safe"> ...text and logos... </div></div>
```
Remove the `debug` class for the final render.

## ffmpeg
Shrink a finished video into the safe area:
```bash
python scripts/autofix.py fit frame.png --preset ig-reel --out /dev/null   # prints the ffmpeg filter
ffmpeg -i in.mp4 -vf "scale=960:1440:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black" out.mp4
```
Burn the guide into a preview copy (not for posting):
```bash
ffmpeg -i in.mp4 -i assets/guides/ig-reel.png -filter_complex "overlay" preview.mp4
```

## Canva, CapCut, Premiere, DaVinci, Figma
1. Create the canvas at the preset size (for example 1080 x 1920).
2. Place `assets/guides/<preset>.png` on top and lock it.
3. Keep everything important in the green box and out of the red.
4. Hide or delete the guide layer before export.

## Python (Pillow, MoviePy, OpenCV)
```python
import sys; sys.path.insert(0, "scripts")
import zones_lib as Z
p = Z.preset("ig-reel")
x, y, w, h = Z.safe_rect(p)       # place text inside this
avoid = Z.avoid_rects(p)          # keep clear of these
```

## Custom platform
Copy a preset in `zones.json`, change the numbers, then regenerate:
```bash
python scripts/export_zones.py css > templates/safezone.css
python scripts/export_zones.py ts  > templates/zones.ts
python scripts/make_guides.py --all
```
