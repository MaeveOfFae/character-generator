# Seed List Generator (seed output/)

Goal: generate a list of unique seeds for RPBotGenerator.

1) Ask me for:
   - count (e.g., 25, 50)
   - tags/genres (optional)
   - any hard constraints (e.g., "no fantasy", "more noir", "non-romance")

2) Generate seeds that each imply:
   - a power dynamic
   - an emotional temperature
   - a tension axis
   - why {{user}} matters (as role/leverage/connection anchor)

3) Output format MUST be:
   - seeds only
   - no headings
   - no numbering
   - one seed per line

4) Safety/format constraints:
   - seeds may reference {{user}} only as an anchor (role/leverage/dependency/obligation)
   - never assert {{user}} actions, choices, dialogue, thoughts, emotions, sensations, or consent

5) Save results into:
   seed output/<descriptive_filename>.txt
