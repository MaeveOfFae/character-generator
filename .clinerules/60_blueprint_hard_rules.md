# Blueprint Hard Rules (Module-Specific)

These are non-negotiable.

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
- Follow section order and field names EXACTLY.
- Fill every bracketed placeholder (no "[Age]" etc left unfilled).
- Keep lists tight and functional; paragraphs brief.
- No moral sanitization unless content mode demands it.
- Output ONLY inside a single plaintext code block. No commentary.

## intro_scene
- Second-person narrative only.
- Don’t rush; let beats land; no generic openings.
- Must end with an open loop inviting a response from {{user}} (without narrating what {{user}} does next).
- Output ONLY inside a single plaintext code block. No commentary.

## intro_page (HTML)
- Single HTML snippet with self-contained styling (no external assets/CSS).
- Replace every {PLACEHOLDER} token with concrete values; leave none.
- Hard-ban: never emit example/prior character names.
- Output must be immediately usable as pasted HTML.

## a1111
- Replace all ((...)) slots with concrete tags; leave no placeholders.
- Set [Content: SFW|NSFW] to match content mode (default NSFW).
- Keep tag/syntax structure intact.
- Output ONLY in a plaintext code block.

## suno
- Maintain the [Control] block structure and the exact section headers.
- Do not leave placeholders like "{TITLE}" unfilled.
- Output ONLY inside a single plaintext code block. No commentary.
