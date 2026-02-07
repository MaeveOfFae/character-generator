List the inputs that must be treated as untrusted in this system/feature.

Instructions
- Enumerate all input sources (user input, headers, cookies, webhooks, files, third-party APIs, environment/config, database contents).
- For each, explain the primary risks and required validation/sanitization.
- Call out trust boundaries explicitly (where data changes trust level, if ever).

Output
- A table or bullet list of untrusted inputs with required controls (validation, encoding, authorization, rate limits).
