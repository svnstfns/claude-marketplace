# ARCH-dataflow

> arc42 §6 — Runtime View. How the system behaves at runtime for the main scenarios.

## Scenario 1 — <Name of main use case>

**Trigger:** <What initiates this flow.>
**Actors:** <User, external system, scheduler, ...>

```mermaid
sequenceDiagram
    actor User
    participant UI
    participant API
    participant DB

    User->>UI: <action>
    UI->>API: POST /resource
    API->>DB: INSERT
    DB-->>API: ok
    API-->>UI: 201
    UI-->>User: <feedback>
```

**Failure modes:**
- <Component fails> → <What happens, how recovered>

---

## Scenario 2 — <Name>

...
