Mentally profile the described system/code and identify likely performance hotspots.

Instructions
- Identify the most expensive operations (I/O, database queries, serialization, N+1 patterns, contention, allocations).
- Explain why each is likely a hotspot and what symptoms it would cause.
- Propose what to measure first (metrics, tracing spans, benchmarks) to validate.

Output
- A ranked list of suspected hotspots with measurement recommendations.
