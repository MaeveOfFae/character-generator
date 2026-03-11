# Blueprint Hard Rules (Module-Specific)

These are non-negotiable.

Apply only the sections relevant to the active template. Do not force modules from one template into another.

## system_prompt

- Total output under 300 tokens.
- Paragraphs only (no bullets, lists, or headings).
- No template placeholders.
- Output ONLY inside a single plaintext code block. No commentary.

## post_history

- Total output under 300 tokens.
- Paragraph form only (no bullets, lists, or section headers).
- Use {{original}} to extend/refine if present; never overwrite/negate it.
- Output ONLY inside a single plaintext code block. No commentary.

## character_sheet

- **CRITICAL: Use ONLY the structure shown in the blueprint. Do NOT use alternative formats like [Character]/[Profile]/[Attributes] sections.**
- **Field names must match EXACTLY: "name:", "age:", "occupation:", "heritage:", "Core Concept:", "Appearance:", "Personality:", "Strengths:", "Flaws:", etc.**
- Follow section order and field names EXACTLY as shown in the blueprint.
- Fill every bracketed placeholder (no "[Age]", "[Name]", "[Strength]" left unfilled).
- Keep lists tight and functional; paragraphs brief.
- No moral sanitization unless content mode demands it.
- Output ONLY inside a single plaintext code block. No commentary.

## Aksho split profile assets

- `char_basic_info`, `char_physical`, `char_clothing`, `char_personality`, and `char_background` must follow their own blueprint structures exactly.
- Do not collapse split-profile templates back into a legacy `character_sheet`.
- Preserve the dependency intent between those assets: later profile assets may refine earlier ones, but must not contradict them.
- Output each asset inside its own plaintext code block. No commentary.

## intro_scene

- Second-person narrative only.
- Don’t rush; let beats land; no generic openings.
- Must end with an open loop inviting a response from {{user}} (without narrating what {{user}} does next).
- Output ONLY inside a single plaintext code block. No commentary.

## initial_message

- Follow the active template's opener blueprint exactly.
- Keep `{{user}}` un-authored.
- If the opener is conversation-style rather than scene-paragraph style, preserve that blueprint-specific format instead of forcing `intro_scene` rules onto it.
- Output ONLY inside a single plaintext code block. No commentary.

## intro_page (Markdown)

- Single Markdown snippet (no HTML/CSS).
- Replace every {PLACEHOLDER} token with concrete values; leave none.
- Hard-ban: never emit example/prior character names.
- Output ONLY inside a single plaintext code block. No commentary.

## a1111

- Replace all ((...)) slots with concrete tags; leave no placeholders.
- Set [Content: SFW|NSFW] to match content mode (default NSFW).
- Keep tag/syntax structure intact.
- Output ONLY in a plaintext code block.

## suno

- Maintain the [Control] block structure and the exact section headers.
- Do not leave placeholders like "{TITLE}" unfilled.
- Output ONLY inside a single plaintext code block. No commentary.

## Template contract rule

- Only emit modules that the selected template actually declares.
- If a template omits `a1111` or `suno`, do not invent them.
- If a template adds profile or opener assets not listed above, follow the exact local blueprint and preserve the same isolation discipline.
