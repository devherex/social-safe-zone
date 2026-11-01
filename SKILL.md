---
name: social-safe-zone
description: Keeps all text, logos, captions, CTAs and faces inside the safe zone of Instagram Reels, Stories, Feed, TikTok, YouTube Shorts and LinkedIn when making videos, reels, carousels, thumbnails or graphics. Use this skill whenever the user asks for a reel, story, short, TikTok, social video, post graphic, promo video or any 9:16 / 4:5 / 1080x1920 / 1080x1350 design, even if they never say "safe zone". Also use it to check, auto-fix or preview an existing design or video against platform UI overlap (buttons, captions, profile bar, grid crop).
---

# Social Safe Zone

Platform apps cover parts of your frame with buttons, captions and the profile bar, and the profile grid crops the sides. Anything important there gets hidden. This skill makes sure it never happens.

All numbers live in `zones.json`. Never hard-code them. List presets: `python scripts/zones_lib.py list`.

## Workflow (follow in order)

1. **Pick the preset.** Match the platform: `ig-reel`, `ig-story`, `ig-story-strict`, `ig-feed`, `tiktok`, `yt-shorts`, `linkedin-4x5`, `linkedin-16x9`. If the user names no platform, assume `ig-reel`. If they want several platforms, design one master with the strictest zone, then check the others.
2. **Read the zone.** `python scripts/zones_lib.py show <preset>` prints the safe rectangle and the avoid boxes.
3. **Build inside it.**
   - Full-bleed backgrounds and footage may fill the whole frame.
   - Everything important goes inside the safe rectangle: headlines, body text, subtitles, logos, faces, CTA buttons, key product shots.
   - Never place anything in an `avoid` box (Reels: the button column at the bottom right).
   - Subtitles sit in the lower part of the safe area, never on the bottom margin.
   - Min text size: 42px at 1080 wide. High contrast on every background.
   - Reels and Feed: keep key content inside the grid crop too, so the profile grid thumbnail still reads.
4. **Use the right helper for the tool:**
   - Remotion / React: `templates/SafeZone.tsx` and `templates/zones.ts`
   - HTML / CSS: `templates/safezone.css` (classes like `sz-ig-reel`)
   - Python / Pillow / ffmpeg: `scripts/zones_lib.py`
   - Canva / CapCut / Premiere: drop `assets/guides/<preset>.png` on top as a locked layer
   - More detail: `references/integrations.md`
5. **Verify before delivering.**
   - Layout JSON (exact): `python scripts/check_zones.py layout.json`
   - Image or video: `python scripts/check_zones.py file --preset <preset> --overlay check.png` (add `--ocr` if tesseract exists)
   - Fake app preview: `python scripts/preview_mock.py frame.png --preset <preset> --out mock.png`
6. **Fix and re-check.** `python scripts/autofix.py layout.json` moves or scales elements. For finished footage that cannot be re-laid out: `python scripts/autofix.py fit in.png --preset <preset> --out out.png`.
7. **Tell the user** the result in one line: preset used, PASS or FAIL, and what was moved. Show the overlay or mock preview if it helps.

## Layout JSON (for exact checks and auto-fix)

```json
{"preset": "ig-reel", "elements": [
  {"id": "headline", "type": "text", "text": "Hello", "x": 60, "y": 300, "w": 700, "h": 90, "size": 90},
  {"id": "logo", "type": "box", "x": 60, "y": 1500, "w": 220, "h": 110},
  {"id": "bg", "type": "box", "x": 0, "y": 0, "w": 1080, "h": 1920, "important": false}
]}
```

`important: false` marks backgrounds that may bleed outside the zone.

## Rules

- If the user explicitly wants something inside a danger area, do it but say what may be covered.
- Values marked `estimate` in `zones.json` are community-measured, not official. Mention this for client work and suggest a test post.
- To add a platform or change a number, edit `zones.json` only, then run `python scripts/export_zones.py css > templates/safezone.css` and `python scripts/make_guides.py --all`.
