#!/bin/bash

# RPBotGenerator Character Export Script
# Usage:
#   1) From files (recommended):
#      ./export_character.sh "character_name" "source_dir"
#      ./export_character.sh "character_name" "source_dir" "llm_model"
#   2) From inline text (legacy):
#      ./export_character.sh "character_name" "system_prompt" "post_history" "character_sheet" "intro_scene" "intro_page" "a1111_prompt" "suno_prompt"

if [ "$#" -ne 2 ] && [ "$#" -ne 3 ] && [ "$#" -ne 8 ]; then
    echo "Error: Invalid arguments"
    echo "Usage (recommended): $0 character_name source_dir [llm_model]"
    echo "Usage (legacy):      $0 character_name system_prompt post_history character_sheet intro_scene intro_page a1111_prompt suno_prompt"
    exit 1
fi

CHARACTER_NAME="$1"

sanitize() {
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/_/g; s/_+/_/g; s/^_+|_+$//g'
}

CHARACTER_NAME_SANITIZED="$(sanitize "$CHARACTER_NAME")"
MODEL_SUFFIX=""

if [ "$#" -eq 3 ]; then
    MODEL_SUFFIX="($(sanitize "$3"))"
fi

# Create output directory
OUTPUT_DIR="output/${CHARACTER_NAME_SANITIZED}${MODEL_SUFFIX}"
mkdir -p "$OUTPUT_DIR"

if [ "$#" -eq 2 ] || [ "$#" -eq 3 ]; then
    SOURCE_DIR="$2"
    for f in system_prompt.txt post_history.txt character_sheet.txt intro_scene.txt a1111_prompt.txt suno_prompt.txt intro_page.html; do
        if [ ! -f "${SOURCE_DIR}/${f}" ]; then
            echo "Error: Missing ${SOURCE_DIR}/${f}"
            exit 1
        fi
    done

    cp "${SOURCE_DIR}/system_prompt.txt" "$OUTPUT_DIR/system_prompt.txt"
    cp "${SOURCE_DIR}/post_history.txt" "$OUTPUT_DIR/post_history.txt"
    cp "${SOURCE_DIR}/character_sheet.txt" "$OUTPUT_DIR/character_sheet.txt"
    cp "${SOURCE_DIR}/intro_scene.txt" "$OUTPUT_DIR/intro_scene.txt"
    cp "${SOURCE_DIR}/intro_page.html" "$OUTPUT_DIR/intro_page.html"
    cp "${SOURCE_DIR}/a1111_prompt.txt" "$OUTPUT_DIR/a1111_prompt.txt"
    cp "${SOURCE_DIR}/suno_prompt.txt" "$OUTPUT_DIR/suno_prompt.txt"
else
    SYSTEM_PROMPT="$2"
    POST_HISTORY="$3"
    CHARACTER_SHEET="$4"
    INTRO_SCENE="$5"
    INTRO_PAGE="$6"
    A1111_PROMPT="$7"
    SUNO_PROMPT="$8"

    echo "$SYSTEM_PROMPT" > "$OUTPUT_DIR/system_prompt.txt"
    echo "$POST_HISTORY" > "$OUTPUT_DIR/post_history.txt"
    echo "$CHARACTER_SHEET" > "$OUTPUT_DIR/character_sheet.txt"
    echo "$INTRO_SCENE" > "$OUTPUT_DIR/intro_scene.txt"
    echo "$INTRO_PAGE" > "$OUTPUT_DIR/intro_page.html"
    echo "$A1111_PROMPT" > "$OUTPUT_DIR/a1111_prompt.txt"
    echo "$SUNO_PROMPT" > "$OUTPUT_DIR/suno_prompt.txt"
fi

echo "✓ Character '${CHARACTER_NAME}' exported to ${OUTPUT_DIR}/"
echo "  - system_prompt.txt"
echo "  - post_history.txt"
echo "  - character_sheet.txt"
echo "  - intro_scene.txt"
echo "  - intro_page.html"
echo "  - a1111_prompt.txt"
echo "  - suno_prompt.txt"
