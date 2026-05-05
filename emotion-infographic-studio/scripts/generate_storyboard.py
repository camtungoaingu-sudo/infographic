#!/usr/bin/env python3
"""
generate_storyboard.py
Build a storyboard PNG from a Python data dict.
This is the script Claude should call after filling in all data.
"""

import html
import os, sys, json, textwrap
from pathlib import Path
from playwright.sync_api import sync_playwright

TEMPLATE_PATH = Path(__file__).parent / "storyboard_template.html"


def _escape(value) -> str:
    return html.escape(str(value or ""), quote=True)


def _asset_uri(src) -> str:
    if src and os.path.isfile(src):
        return Path(src).resolve().as_uri()
    return ""

# ──────────────────────────────────────────────────────────────
# SCENE HTML BUILDER
# ──────────────────────────────────────────────────────────────
def build_scene(scene: dict, idx: int) -> str:
    num = str(idx).zfill(2)
    
    def frame_img(src, label):
        if src and os.path.isfile(src):
            return f'<img src="{_asset_uri(src)}" alt="{_escape(label)}">'
        return f'<div class="img-placeholder">{_escape(label)}<br>(reference)</div>'

    camera_items = "".join(
        f'<div class="note-item">{c}</div>' for c in scene.get("camera", [])
    )
    audio_items = "".join(
        f'<div class="note-item audio">🔊 {a}</div>' for a in scene.get("audio_cues", [])
    )

    return f"""
<div class="sb-scene">
  <!-- Label -->
  <div class="scene-label">
    <div class="scene-num">{num}</div>
    <div class="scene-time">{scene.get('time','')}</div>
    <div class="scene-name">Scene {num}</div>
    <div class="scene-title">{scene.get('title','')}</div>
  </div>

  <!-- Frames -->
  <div class="scene-frames">
    <div class="frame-header">
      <span>Frame 1</span><span></span><span>Frame 2</span>
    </div>
    <div class="frames-row">
      <div class="frame-img">{frame_img(scene.get('frame1_img'), scene.get('frame1_label','Frame 1'))}</div>
      <div class="frame-arrow">→</div>
      <div class="frame-img">{frame_img(scene.get('frame2_img'), scene.get('frame2_label','Frame 2'))}</div>
    </div>
    <div class="scene-caption">{scene.get('caption','')}</div>
  </div>

  <!-- Notes -->
  <div class="scene-notes">
    <div class="note-block">
      <div class="note-title"><span class="icon">📷</span> CAMERA / MOVEMENT</div>
      {camera_items}
    </div>
    <div class="note-block">
      <div class="note-title"><span class="icon">🔊</span> AUDIO CUES</div>
      {audio_items}
    </div>
  </div>
</div>
"""


# ──────────────────────────────────────────────────────────────
# MAIN GENERATOR
# ──────────────────────────────────────────────────────────────
def generate(data: dict, output_png: str, width: int = 1400):
    tpl = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Product image
    def img_tag(src, cls="", style=""):
        if src and os.path.isfile(src):
            return f'<img src="{_asset_uri(src)}" class="{_escape(cls)}" style="{_escape(style)}">'
        return f'<div class="img-placeholder">{_escape(src or "Product image")}</div>'

    tpl = tpl.replace("{{BRAND_NAME}}", data.get("brand_name", "Brand"))
    tpl = tpl.replace("{{CLIP_DURATION}}", data.get("clip_duration", "15s"))
    tpl = tpl.replace("{{PRODUCT_DESC}}", data.get("product_desc", ""))
    tpl = tpl.replace("{{TARGET}}", data.get("target", ""))
    tpl = tpl.replace("{{ASPECT}}", data.get("aspect", "9:16 video plan"))

    tpl = tpl.replace("{{PRODUCT_IMAGE_TAG}}", img_tag(data.get("product_image")))
    tpl = tpl.replace("{{HERO_CIRCLE_IMAGE_TAG}}", img_tag(data.get("hero_circle_image")))
    tpl = tpl.replace("{{PRODUCT_LOCK_DESC}}", data.get("product_lock_desc", ""))

    tpl = tpl.replace("{{BGM_DESC}}", data.get("bgm", ""))
    tpl = tpl.replace("{{ROOM_DESC}}", data.get("room", ""))
    tpl = tpl.replace("{{AUDIO_LOGO_DESC}}", data.get("audio_logo", ""))

    tpl = tpl.replace("{{BUYER}}", data.get("buyer", ""))
    tpl = tpl.replace("{{WEARER}}", data.get("wearer", ""))
    tpl = tpl.replace("{{VIEWER}}", data.get("viewer", ""))
    tpl = tpl.replace("{{FRICTION}}", data.get("friction", ""))

    # Scenes
    scenes_html = "".join(build_scene(s, i+1) for i, s in enumerate(data.get("scenes", [])))
    tpl = tpl.replace("{{SCENES_HTML}}", scenes_html)

    # Footer
    tpl = tpl.replace("{{PRODUCTION_NOTES}}", data.get("production_notes", ""))
    
    hooks = "".join(f'<li><span class="dot">●</span>{h}</li>' for h in data.get("opening_hooks", []))
    tpl = tpl.replace("{{OPENING_HOOKS}}", hooks)
    
    donts = "".join(f'<li><span class="cross">✕</span>{d}</li>' for d in data.get("do_not_do", []))
    tpl = tpl.replace("{{DO_NOT_DO}}", donts)
    
    tpl = tpl.replace("{{CALL_TO_ACTION}}", data.get("call_to_action", ""))

    # Write temp HTML
    tmp_html = Path(output_png).with_suffix(".tmp.html")
    tmp_html.write_text(tpl, encoding="utf-8")

    # Render to PNG
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.goto(tmp_html.resolve().as_uri(), wait_until="networkidle")
        full_h = page.evaluate("document.body.scrollHeight")
        page.set_viewport_size({"width": width, "height": full_h})
        page.screenshot(path=output_png, full_page=True)
        browser.close()

    tmp_html.unlink(missing_ok=True)
    print(f"Storyboard saved: {output_png} ({width}x{full_h}px)")
    return output_png


# ──────────────────────────────────────────────────────────────
# DEMO — chạy thử với dữ liệu mẫu từ ảnh gốc
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    demo_data = {
        "brand_name": "Reel Girls Fish",
        "clip_duration": "15s",
        "product_desc": "black front-print fishing tee",
        "target": "US/EN",
        "aspect": "9:16 video plan",
        "product_image": None,       # đặt đường dẫn ảnh thật nếu có
        "hero_circle_image": None,
        "product_lock_desc": "full-front bass print,\npink cap + sunglasses,\ntext \"REEL GIRLS FISH!\"",
        "bgm": "dry swamp-rock, brushed snare + muted guitar, around 92 BPM",
        "room": "dawn boat-ramp hardware, cotton movement, tackle latch",
        "audio_logo": "two reel clicks + muted guitar stop at 14.6-15.0s",
        "buyer": "self or gift giver",
        "wearer": "girl who fishes",
        "viewer": "dock-day insider",
        "friction": "cute, not fake",
        "scenes": [
            {
                "time": "0.0 – 3.2s",
                "title": "Tailgate check",
                "frame1_label": "Model at tailgate",
                "frame2_label": "Shirt print close-up",
                "caption": "No dialogue / no VO. Hands smooth the hem; the print answers first.",
                "camera": ["medium close-up", "slow push-in"],
                "audio_cues": ["cotton brush at 1.0s", "tackle latch tick at 2.2s"],
            },
            {
                "time": "3.2 – 6.8s",
                "title": "Ramp nod",
                "frame1_label": "Walking the dock",
                "frame2_label": "Rack focus reveal",
                "caption": "No dialogue / no VO. The dock reads the joke before anyone explains it.",
                "camera": ["handheld tracking", "rack focus"],
                "audio_cues": ["rod butt tap at 4.7s"],
            },
            {
                "time": "6.8 – 10.8s",
                "title": "Cast prep",
                "frame1_label": "Handling pink lure",
                "frame2_label": "Macro lock-off on gear",
                "caption": "No dialogue / no VO. Pink lure, bass print, real hands on gear.",
                "camera": ["over-the-shoulder", "macro lock-off"],
                "audio_cues": ["reel ratchet at 8.4s"],
            },
            {
                "time": "10.8 – 15.0s",
                "title": "Keep photo",
                "frame1_label": "Holding shirt forward",
                "frame2_label": "Phone photo moment",
                "caption": "No dialogue / no VO. The tee becomes the photo anchor.",
                "camera": ["static hold", "pull out"],
                "audio_cues": ["cooler thud at 12.2s", "reel-click logo at 14.6-15.0s"],
            },
        ],
        "production_notes": "Hold the print readable before any laugh or cast. Keep hands on hems, rod, tackle, never over the words. Use dock hardware and real fishing prep, not costume props.",
        "opening_hooks": [
            "Before the first cast, the shirt answers the look.",
            "At the dock rail, the pink bass starts the joke.",
            "Back at the truck, it becomes the photo everyone wants.",
        ],
        "do_not_do": [
            "No fake back print.",
            "No category-label opener.",
            "No glossy fashion studio.",
        ],
        "call_to_action": "Choose the tee that earns the nod before the first cast.",
    }

    out = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/outputs/storyboard.png"
    generate(demo_data, out)
