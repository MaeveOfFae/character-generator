# Export Character Bundle

Goal: export a character bundle from a source directory using tools/export_character.sh.

1) Ask me for:
   - character_name
   - source_dir (where the generated asset files live)
   - llm_model (optional; used in output naming)

2) Confirm that source_dir contains:
   system_prompt, post_history, character_sheet, intro_scene, intro_page, a1111, suno

3) Run:
   ./tools/export_character.sh "character_name" "source_dir" "llm_model"

4) Report the output directory path and list the files produced.
