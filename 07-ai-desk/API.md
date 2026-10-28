# API v1

All endpoints use the same origin as the UI. JSON errors from DRF include detail; domain errors include error. Every response has X-Request-ID. Authentication failures are 403 except invalid login credentials (401). Mutations require X-CSRFToken from GET /api/v1/session. Session cookie: aidesk_session.

| Endpoint | Methods | Input / output |
|---|---|---|
| `/api/v1/health` | GET | status, service, encoder_ready |
| `/api/v1/session` | GET | csrf, user {name, role} or null |
| `/api/v1/login` | POST | username/password → user, rotated csrf |
| `/api/v1/logout` | POST | ok |
| `/api/v1/chats` | GET, POST | own chat list / create chat |
| `/api/v1/chats/{id}` | GET, DELETE | own messages / delete own chat |
| `/api/v1/chats/{id}/ask` | POST | text (1–2000 chars), language pl/en; SSE events sources/token/done/error |
| `/api/v1/documents` | GET, POST | permitted list / multipart file, access all/staff/admin, language pl/en |
| `/api/v1/sources/{id}` | GET | accessible chunk title/text/position |

Errors: 400 invalid input; 403 permissions or CSRF; 404 absent or inaccessible resource; 429 throttled; 503 search/extraction unavailable. After SSE headers are sent, generation errors arrive as an error event, not HTTP 503. POST ask persists the question even when generation fails so the question remains visible in history.

GET /api/v1/health is process liveness only. GET /api/v1/readiness performs a real CPU embedding probe, verifies the index and the configured local Ollama model; 503 means not ready. Cold readiness may take time to load encoder weights.
