# Generate Full Suite from SEED (RPBotGenerator)

Goal: compile ONE seed into the full asset suite using rpbotgenerator.md, with strict ordering and blueprint compliance.

1) Ask me for:
   - SEED (one line)
   - Mode (optional): SFW / NSFW / Platform-Safe
   - Output target:
     a) codeblocks only
     b) write files to /output/<character_name>(<llm_model>) if supported

2) Open and read:
   - rpbotgenerator.md
   - system_prompt.md, post_history.md, character_sheet.md, intro_scene.md, intro_page.md, a1111.md, suno.md

3) Validate the seed per rpbotgenerator.md:
   - Must imply: power dynamic, emotional temperature, tension axis, why {{user}} matters (as anchor, not actor)

4) Compile the suite in EXACT order:
   system_prompt → post_history → character_sheet → intro_scene → intro_page → a1111 → suno
   - Output only asset codeblocks/files (and Adjustment Note if required).

5) Final checks before sending/writing:
   - No placeholders remain ({PLACEHOLDER}, ((...)), {TITLE}, bracket fields)
   - Mode respected across all assets
   - No narrating {{user}} actions/thoughts/consent
   - No contradictions across assets
