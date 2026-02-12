---
name: A1111_SDXL_ComfyUI
description: SDXL-first modular prompt blueprint compatible with AUTOMATIC1111 and ComfyUI.
version: 4.0
---

# SDXL Prompt Blueprint (AUTOMATIC1111 + ComfyUI)

Produce the image prompt using the **SDXL Modular Character Prompt Template** below.

Output rules (strict):

- Replace **all** `((...))` slots with concrete text derived from the seed (no placeholders left behind).
- Set `[Content: SFW|NSFW]` to match the orchestrator content mode when present (default **NSFW**).
- SDXL prefers **descriptive phrases / short sentences** over long tag soups. Use commas to separate phrases.
- Keep prompts **tight**. Prefer 1–3 lines of meaningful description over long “quality tag” dumps.
- Use weights sparingly. See weighting rules per UI.

---

## Why this version is different (SDXL-first)

SDXL responds best to:
- clear subject + setting + lighting + style phrased in natural language,
- fewer generic “masterpiece/best quality” spam terms,
- concise negatives focused on real failure modes (hands, watermark, blur).

---

## 🧩 CONTROL TEMPLATE (UI-agnostic)

```plaintext
[Control]
[Title: Character Portrait]
[Model: SDXL]
[Content: SFW|NSFW]

[Subject: ((subject)), ((age descriptor)), ((role/occupation)), ((heritage/phenotype))]
[Identity: ((core look)), ((signature detail)), ((hair/eyes)), ((wardrobe/materials))]
[Pose: ((pose/framing)), ((gesture/hand action)), ((body language))]
[Expression: ((emotion)), ((microexpression)), ((gaze direction))]
[Action: ((what they are doing)), ((prop interaction))]
[Setting: ((environment)), ((time/weather)), ((background story cue))]
[Lighting: ((lighting style)), ((key light direction)), ((color temperature))]
[Camera: ((shot type)), ((lens/feel)), ((depth of field))]
[Style: ((medium/render)), ((genre aesthetic)), ((palette bias)), ((texture/grain))]
[Safety: ((sfw/nsfw constraints in plain language))]
[Notes: ((anything critical that must not change))]

[Recommended SDXL Base Size]
1024x1024 (or 832x1216 / 1216x832)

[Sampler/CFG Suggestions]
- Start: DPM++ 2M Karras (or similar), 25–35 steps
- CFG: 4.5–7 (lower for realism, higher for stylized)
- If using SDXL Refiner: switch around 0.75–0.85 of steps
```

---

## ✅ AUTOMATIC1111 — SDXL Prompt Output

> Use A1111’s normal Prompt / Negative Prompt fields.
> A1111 **normalizes** weights across tokens; moderate weights are usually enough.

```plaintext
[A1111 Positive Prompt]
((subject)), ((age descriptor)), ((role/occupation)), ((heritage/phenotype)).
((core look)), ((signature detail)). ((hair/eyes)). ((wardrobe/materials)).
((pose/framing)), ((gesture/hand action)), ((body language)).
((emotion)), ((microexpression)), ((gaze direction)).
((what they are doing)), ((prop interaction)).
In/at ((environment)) during ((time/weather)); ((background story cue)).
((lighting style)), key light from ((key light direction)), ((color temperature)).
((shot type)), ((lens/feel)), shallow depth of field.
((medium/render)), ((genre aesthetic)), ((palette bias)), ((texture/grain)).
((sfw/nsfw constraints in plain language)).
((a1111_lora_tags))

[A1111 Negative Prompt]
low quality, blurry, out of focus, jpeg artifacts,
bad anatomy, bad proportions, deformed, distorted,
extra limbs, extra fingers, missing fingers, malformed hands,
text, watermark, signature, logo,
overexposed, underexposed, muddy colors, oversaturated,
((sfw_negative_extras))
```

### A1111 Weighting rules (SDXL)
- Prefer **no weights** unless fixing a specific issue.
- If needed: keep to ~`1.05–1.30` (example: `((signature detail:1.15))`).
- Don’t weight *everything*. Pick one or two critical phrases.

### A1111 LoRA usage
- Use: `<lora:((lora_name)):((lora_strength))>`
- Keep strengths conservative for SDXL: `0.5–0.9` unless the LoRA author says otherwise.
- Put LoRA tags in `((a1111_lora_tags))` (can be empty).

---

## ✅ ComfyUI — SDXL Prompt Output

> ComfyUI uses **raw** weights (no A1111 normalization). If you port prompts from A1111, reduce weights.
> Put these into your **CLIP Text Encode (Prompt)** and **CLIP Text Encode (Negative)** nodes.

```plaintext
[ComfyUI Positive Prompt]
((subject)), ((age descriptor)), ((role/occupation)), ((heritage/phenotype)),
((core look)), ((signature detail)), ((hair/eyes)), ((wardrobe/materials)),
((pose/framing)), ((gesture/hand action)), ((body language)),
((emotion)), ((microexpression)), ((gaze direction)),
((what they are doing)), ((prop interaction)),
((environment)), ((time/weather)), ((background story cue)),
((lighting style)), key light from ((key light direction)), ((color temperature)),
((shot type)), ((lens/feel)), shallow depth of field,
((medium/render)), ((genre aesthetic)), ((palette bias)), ((texture/grain)),
((sfw/nsfw constraints in plain language)),
((comfy_trigger_words))

[ComfyUI Negative Prompt]
low quality, blurry, out of focus, jpeg artifacts,
bad anatomy, bad proportions, deformed, distorted,
extra limbs, extra fingers, missing fingers, malformed hands,
text, watermark, signature, logo,
overexposed, underexposed, muddy colors, oversaturated,
((sfw_negative_extras))
```

### ComfyUI Weighting rules (SDXL)
- Prefer **no weights** unless you’re correcting a failure.
- If needed: keep to ~`1.02–1.20`. Example: `(signature detail:1.10)`.
- Avoid square-bracket downweighting reliance; prefer `(term:0.90)` explicitly.

### ComfyUI Embeddings (Textual Inversion)
- Put embedding files in `ComfyUI/models/embeddings/`
- Invoke as: `embedding:((embedding_name))`
- You can weight it: `(embedding:((embedding_name)):1.10)`

### ComfyUI LoRAs
- Use a **Load LoRA** node (or equivalent) and set:
  - `strength_model` ~ `0.5–0.9`
  - `strength_clip` ~ `0.5–1.0` (start equal to model strength)
- If the LoRA requires a trigger word, add it in `((comfy_trigger_words))`.

---

## 🧼 SFW / NSFW handling

- If `[Content: SFW]`, set:
  - `((sfw_negative_extras)) = nude, naked, explicit, porn, fetish, nipples, genitalia`
  - and keep `((sfw/nsfw constraints in plain language))` like: “fully clothed, no nudity, PG-13”
- If `[Content: NSFW]`, set:
  - `((sfw_negative_extras)) =` *(empty)*
  - and put the explicit intent **only** in the positive constraints line (example: “adult nude boudoir photo, explicit nudity”).  
    (If you’re using a safety-filtered checkpoint, you may need an NSFW-capable SDXL model for consistent results.)

---

## 🧠 Category Library (Reference only)

### Subject
- 1 woman / 1 man / androgynous adult / couple / group portrait
- “adult” / “young adult” / “mature adult” (avoid ambiguous age wording)

### Camera
- close-up portrait, head-and-shoulders
- medium shot, waist-up
- full-body, dynamic pose
- 35mm cinematic, 85mm portrait lens feel
- shallow depth of field, creamy bokeh

### Lighting
- soft window light, morning
- golden hour rim light
- dramatic chiaroscuro, moody shadows
- neon spill light, rainy reflections
- candlelight, warm intimate glow

### Style / Texture
- photorealistic editorial photo, subtle film grain
- painterly realism, visible brush texture
- anime-inspired clean shading (use SDXL anime checkpoints/LoRAs)
- low-contrast film look / high-contrast noir
- matte skin highlights / glossy latex reflections

---

## ⚙️ Usage example (SDXL-ready)

```plaintext
[Subject: adult woman, solo, nightclub singer, Mediterranean]
[Identity: sharp bob haircut, smoky eyeliner, black velvet dress, silver ring]
[Pose: waist-up portrait, one hand on mic stand, relaxed shoulders]
[Expression: confident half-smile, direct gaze]
[Setting: smoky jazz bar, late night, blurred crowd]
[Lighting: warm key light, soft rim light, amber tones]
[Camera: cinematic medium shot, 85mm portrait feel, shallow DOF]
[Style: photoreal editorial, subtle film grain, rich blacks]
[Safety: SFW, fully clothed, no nudity]
```

---
