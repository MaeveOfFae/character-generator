#!/bin/bash

# RPBotGenerator Character Export Script
# Usage:
#   1) From files (recommended):
#      ./export_character.sh "character_name" "source_dir"
#      ./export_character.sh "character_name" "source_dir" "llm_model"
#   2) From inline text (legacy):
#      ./export_character.sh "character_name" "system_prompt" "post_history" "character_sheet" "intro_scene" "intro_page" "a1111_prompt" "suno_prompt"
#
# Note: The current V2/V3 Card default flow uses the file-based export path above.

if [ "$#" -ne 2 ] && [ "$#" -ne 3 ] && [ "$#" -ne 8 ]; then
    echo "Error: Invalid arguments"
    echo "Usage (recommended): $0 character_name source_dir [llm_model]"
    echo "Usage (legacy only): $0 character_name system_prompt post_history character_sheet intro_scene intro_page a1111_prompt suno_prompt"
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
    if [ ! -d "$SOURCE_DIR" ]; then
        echo "Error: Source directory not found: $SOURCE_DIR"
        exit 1
    fi

    EXPORTED_FILES=()
    for source_file in "$SOURCE_DIR"/*.txt "$SOURCE_DIR"/*.md; do
        if [ ! -f "$source_file" ]; then
            continue
        fi

        filename="$(basename "$source_file")"
        cp "$source_file" "$OUTPUT_DIR/$filename"
        EXPORTED_FILES+=("$filename")
    done

    if [ "${#EXPORTED_FILES[@]}" -eq 0 ]; then
        echo "Error: No .txt or .md asset files found in $SOURCE_DIR"
        exit 1
    fi
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
    echo "$INTRO_PAGE" > "$OUTPUT_DIR/intro_page.md"
    echo "$A1111_PROMPT" > "$OUTPUT_DIR/a1111_prompt.txt"
    echo "$SUNO_PROMPT" > "$OUTPUT_DIR/suno_prompt.txt"
fi

echo "✓ Character '${CHARACTER_NAME}' exported to ${OUTPUT_DIR}/"
if [ "$#" -eq 2 ] || [ "$#" -eq 3 ]; then
    for exported_file in "${EXPORTED_FILES[@]}"; do
        echo "  - $exported_file"
    done
else
    echo "  - system_prompt.txt"
    echo "  - post_history.txt"
    echo "  - character_sheet.txt"
    echo "  - intro_scene.txt"
    echo "  - intro_page.md"
    echo "  - a1111_prompt.txt"
    echo "  - suno_prompt.txt"
fi
