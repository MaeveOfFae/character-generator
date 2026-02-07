Design production guardrails for this LLM-powered output.

Instructions
- Define what “safe and correct enough” means (policy, factuality, format, tone, allowed actions).
- Add layered defenses:
  - Input hardening (prompt injection resistance, allowlists, context filtering).
  - Output constraints (schemas, structured formats, constrained generation where possible).
  - Validation (rule checks, schema validation, safety filters, unit tests for prompts).
  - Human-in-the-loop for high-risk actions.
  - Fallback behaviors (safe defaults, refusal, degraded mode).
- Include observability (logging, redaction, metrics, tracing) and continuous evaluation (offline tests, canaries).

Output
- A guardrail plan with concrete mechanisms, enforcement points, and a rollout/monitoring checklist.
