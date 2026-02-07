Generate two implementations of the described feature: a minimal baseline and a hardened version.

Version 1 (minimal)
- Implement only the core happy path.
- Keep it as small as possible while still correct.

Version 2 (hardened)
- Add input validation, error handling, and edge case coverage.
- Improve ergonomics (clear naming, helpful errors, safe defaults).
- Add any necessary safeguards (timeouts, retries, backoff, limits) if applicable.

Output
- Clearly label `V1` and `V2`.
- Summarize what changed from `V1` → `V2` and why.
