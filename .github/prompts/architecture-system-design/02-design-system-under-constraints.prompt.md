Design a system that solves the described problem under the stated constraints.

Instructions
- State assumptions explicitly (inputs, traffic, latency, data size, failure tolerance, compliance).
- Describe the architecture: components, responsibilities, and data flows.
- Identify bottlenecks and limiting resources (CPU, memory, I/O, DB locks, queues, external APIs).
- Explain what breaks first under load and what user-visible symptoms appear.
- Propose mitigations and scaling levers (caching, batching, backpressure, sharding, async work, rate limits).

Output
- Architecture description with clear component boundaries.
- Assumptions list.
- Bottlenecks + “breaks first” analysis.
- Concrete next steps to validate the design (load test plan, instrumentation, capacity estimates).
