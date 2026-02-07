Identify which parts of this system should not rely on an LLM.

Instructions
- List tasks that require determinism, strict correctness, or verifiability (auth, billing, permissions, data integrity, safety-critical actions).
- Explain why an LLM is risky for each (hallucination, nondeterminism, prompt injection, latency/cost, drift).
- Propose non-LLM alternatives or guardrailed patterns (rules/validators, traditional ML, retrieval + verification, human review).

Output
- A “no-LLM zone” list with recommended approaches for each area.
