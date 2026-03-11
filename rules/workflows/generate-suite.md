# Generate Full Suite from SEED (RPBotGenerator)

Goal: compile ONE seed into the full asset suite using `blueprints/system/rpbotgenerator.md`, with strict ordering and blueprint compliance.

1) Ask me for:
   - SEED (one line)
   - Mode (optional): SFW / NSFW / Platform-Safe
   - Output target:
     a) codeblocks only
     b) write files to /output/<character_name>(<llm_model>) if supported

2) Open and read:
   - `blueprints/system/rpbotgenerator.md`
   - `blueprints/templates/official_v2v3/assets/system_prompt.md`
   - `blueprints/templates/official_v2v3/assets/post_history.md`
   - `blueprints/templates/official_v2v3/assets/character_sheet.md`
   - `blueprints/templates/official_v2v3/assets/intro_scene.md`
   - `blueprints/templates/official_v2v3/assets/intro_page.md`
   - `blueprints/templates/official_v2v3/assets/a1111.md`

3) Validate the seed per `blueprints/system/rpbotgenerator.md`:
   - Must imply: power dynamic, emotional temperature, tension axis, why {{user}} matters (as anchor, not actor)

4) Compile the suite in EXACT order:
   system_prompt → post_history → character_sheet → intro_scene → intro_page → a1111 → suno
   - Output only asset codeblocks/files (and Adjustment Note if required).

5) Final checks before sending/writing:
   - No placeholders remain ({PLACEHOLDER}, ((...)), {TITLE}, bracket fields)
   - Mode respected across all assets
   - No narrating {{user}} actions/thoughts/consent
   - No contradictions across assets
