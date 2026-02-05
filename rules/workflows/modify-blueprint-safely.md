# Modify Blueprint Safely (Regression-Proof)

Goal: make a blueprint change without breaking invariants.

1) Ask me:
   - which blueprint file (system_prompt.md, intro_page.md, etc.)
   - desired change (one sentence)
   - whether this is a format change or content guidance change

2) Open the blueprint and identify:
   - hard rules (token limits, placeholders, output format)
   - failure conditions

3) Apply the smallest possible diff.
   - Do not refactor unrelated sections.
   - Preserve separators and code fences exactly.

4) Run the Validate Outputs workflow on that blueprint’s typical failure patterns.

5) Summarize:
   - what changed
   - what invariant it preserves
