---
name: emotion-infographic-studio
description: Run an end-to-end product creative pipeline from an uploaded product image. Use when the user sends a product photo and asks for a complete storyboard, product infographic, ad treatment, scene images, UGC concept, or video prompt. The skill must write context, plan four scenes with camera and audio, coordinate start and end image generation for each scene, render an infographic PNG, and write a final video-generation prompt.
---

# Emotion Infographic Studio

Orchestrate the whole product image to storyboard pipeline. Do not make the user repeat manual steps. Produce step artifacts and show progress after each phase.

## Output Contract

Create a run folder such as `emotion-infographic-run/<slug>-YYYYMMDD-HHMM/` and save:

1. `01_context.md` and `01_context.json`
2. `02_scene_plan.md` and `02_scene_plan.json`
3. `03_frame_prompts.md`
4. `frames/scene_01_start.png` through `frames/scene_04_end.png` when image generation can save files
5. `04_storyboard_data.json`
6. `05_infographic.png`
7. `06_video_prompt.md`

After each phase, briefly tell the user what was produced and include the file path if available.

## Phase 1: Full Context

Inspect the product image directly. Write a complete campaign context with:

- visible product type, form, color, print/material details, and readable text
- uncertain details that should not be claimed
- target buyer, user/wearer, viewer, use case, pain point
- emotional angle, campaign title, positioning, tone, CTA
- product identity rules that generated images must preserve
- do-not-do constraints

Do not invent hard claims such as fabric composition, pricing, certification, shipping, or discounts unless the user provided them.

## Phase 2: Four-Scene Treatment

Write exactly 4 scenes for a 15-second ad unless the user explicitly asks for a different count. Each scene must include:

- scene number, title, timing, goal
- start frame visual, end frame visual
- overlay/caption or no-VO direction
- camera angle, movement, lens/framing notes
- audio cues, music beat, transition
- emotional beat
- product preservation notes

The scenes should follow this rhythm: instant hook, emotional/use moment, design/proof detail, CTA end card.

## Phase 3: Generate Frame Pairs

Create 8 frame prompts: start and end frame for each of the 4 scenes. Each prompt must preserve the product identity from Phase 1 and include:

- exact visible product text when readable
- product color, key graphic/design elements, and brand/name if known
- composition, setting, camera, lighting, mood
- negative constraints: no changed slogan, no distorted product, no fake claims, no watermark

If image generation is available, generate the 8 images in sequence. Use the uploaded product image as the visual reference whenever the tool supports image references. Keep a consistent product, palette, lighting language, and model/setting continuity across frames.

If image generation is unavailable or cannot save files, still write `03_frame_prompts.md`, explain the limitation, and use the original product image or detail crops as placeholders in `04_storyboard_data.json` so the infographic can still render.

## Phase 4: Render Infographic

Assemble `04_storyboard_data.json` using the bundled renderer schema:

```json
{
  "brand_name": "Brand or campaign title",
  "clip_duration": "15s",
  "product_desc": "short product description",
  "target": "market/language",
  "aspect": "9:16 video plan",
  "product_image": "/absolute/path/to/product.png",
  "hero_circle_image": "/absolute/path/to/detail-or-product.png",
  "product_lock_desc": "visible product lock details",
  "bgm": "music direction",
  "room": "room tone direction",
  "audio_logo": "ending audio logo",
  "buyer": "buyer insight",
  "wearer": "user/wearer insight",
  "viewer": "viewer insight",
  "friction": "purchase tension",
  "scenes": [
    {
      "time": "0.0 - 3.5s",
      "title": "Scene title",
      "frame1_img": "/absolute/path/to/start.png",
      "frame1_label": "start frame label",
      "frame2_img": "/absolute/path/to/end.png",
      "frame2_label": "end frame label",
      "caption": "short action/caption",
      "camera": ["shot note", "movement note"],
      "audio_cues": ["sound cue", "music cue"]
    }
  ],
  "production_notes": "concise notes",
  "opening_hooks": ["hook 1", "hook 2", "hook 3"],
  "do_not_do": ["avoid 1", "avoid 2", "avoid 3"],
  "call_to_action": "CTA"
}
```

Render the board from the plugin root:

```bash
python scripts/generate_from_json.py <run-folder>/04_storyboard_data.json <run-folder>/05_infographic.png --width 1400
```

If Python is not `python`, use the available interpreter. If Playwright is missing, install or report the exact command needed, then continue with all non-render artifacts.

## Phase 5: Video Prompt

Write `06_video_prompt.md` after the infographic data is complete. Include:

- product identity lock and exact text constraints
- visual style, mood, aspect ratio, duration, platform
- scene-by-scene timing, motion, camera, subject action, transition, audio
- references to generated start/end frames when paths exist
- negative prompt section

The prompt must be ready to paste into a video generation system.

## Final Response

Show the generated infographic image when possible, then list the context, scene plan, frame prompts, storyboard JSON, infographic, and video prompt paths. Mention any skipped image-generation or render step plainly.
