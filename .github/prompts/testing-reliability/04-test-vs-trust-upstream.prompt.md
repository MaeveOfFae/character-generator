Decide what should be tested locally versus trusted to upstream dependencies for the described system.

Instructions
- Identify upstream components (frameworks, libraries, managed services, external APIs).
- Specify what you should trust (documented behavior) and what you must verify (your integration assumptions).
- Recommend contract tests and monitoring for dependency behavior that can change.
- Call out where mocking is appropriate vs harmful.

Output
- A clear split: “Test locally” vs “Trust upstream”, with rationale and any contract/monitoring recommendations.
