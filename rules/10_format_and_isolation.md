# Output Format, Isolation, and Ordering

## Output boundaries (STRICT)

- Output NOTHING outside of the required codeblocks/files.
- Each asset must be in its OWN codeblock/file (never combine assets).
- Plaintext unless a blueprint explicitly requires HTML/CSS.

## Ordering (STRICT)

Generate assets in the active template's exact order.

Examples:

1) `V2/V3 Card`: `system_prompt -> post_history -> character_sheet -> intro_scene -> intro_page -> a1111`
2) `Official Aksho`: `system_prompt -> char_basic_info -> char_physical -> char_clothing -> char_personality -> char_background -> post_history -> initial_message`

Do not invent missing assets, and do not assume `suno` is part of the default flow.

Do not print those labels; only output the asset codeblocks.

## Asset isolation rule

- Lower-tier assets may only rely on the seed and higher-tier assets.
- Lower-tier assets must not introduce new facts that higher-tier assets would need.
- The dependency graph comes from the selected template's `depends_on` chain, not from a hardcoded global asset ladder.
