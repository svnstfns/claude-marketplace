# API-<slug>

> Endpoint-by-endpoint specification. Prefer machine-readable schemas (OpenAPI excerpts in fenced YAML).

## Conventions

- Base URL: `<https://host/api>`
- Auth: `<Bearer token | session | none>`
- Content-Type: `application/json`
- Error envelope:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

---

## POST /resource

**Verifies:** REQ-F### (link to functional requirement)
**Purpose:** <Short description>

**Request:**

```yaml
type: object
required: [field_a, field_b]
properties:
  field_a:
    type: string
  field_b:
    type: integer
```

**Responses:**

| Status | Meaning | Body |
|---|---|---|
| 201 | Created | `Resource` schema |
| 400 | Validation error | `Error` envelope |
| 409 | Conflict (duplicate) | `Error` envelope |

**Example:**

```http
POST /api/resource HTTP/1.1
Content-Type: application/json

{"field_a": "value", "field_b": 42}
```

```http
HTTP/1.1 201 Created
Content-Type: application/json

{"id": "uuid", "field_a": "value", "field_b": 42}
```

---

## GET /resource/{id}

...
