# Output Format, Isolation, and Ordering

## Output boundaries (STRICT)

- Output NOTHING outside of the required codeblocks/files.
- Each asset must be in its OWN codeblock/file (never combine assets).
- Plaintext unless a blueprint explicitly requires HTML/CSS.

## Ordering (STRICT)

Generate assets in this exact order:

1) system_prompt
2) post_history
3) character_sheet
4) intro_scene
5) intro_page
6) a1111
7) suno

Do not print those labels; only output the asset codeblocks.

## Asset isolation rule

- Lower-tier assets may only rely on the seed and higher-tier assets.
- Lower-tier assets must not introduce new facts that higher-tier assets would need.
