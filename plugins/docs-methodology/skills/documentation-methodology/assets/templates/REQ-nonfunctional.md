# Non-Functional Requirements

> Every entry must be measurable. No vague adjectives without a number or scenario.
> IDs are zero-padded 3-digit (`REQ-NF001`, `REQ-NF002`, ...).

---

### REQ-NF001 — <Quality attribute / short title>

**Quality attribute:** <Performance | Security | Availability | Maintainability | Usability | Portability | ...>
**Scenario:** <Concrete, measurable scenario. Include the workload, the environment, and the threshold.>

Example: *"A semantic search query over ≤100k chunks returns top-10 results in <500ms at p95 on the reference hardware (8 vCPU / 16GB RAM)."*

**Status:** active
**Tests:** TC-###
**Notes:** <Optional: assumptions, dependencies.>

---

### REQ-NF002 — <Title>

**Quality attribute:** Security
**Scenario:** All API endpoints reject requests without a valid bearer token with HTTP 401 within 50ms.
**Status:** active
**Tests:** TC-###
