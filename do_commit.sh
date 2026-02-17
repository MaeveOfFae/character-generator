#!/bin/bash
cd /home/maeveoffae/Documents/character-generator
git add -A
git commit -F .commit_msg
echo "=== COMMIT STATUS: $? ==="
git branch --show-current
echo "=== CURRENT BRANCH ABOVE ==="
