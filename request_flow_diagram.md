# Request Flow Diagram

## Purpose
This note describes the basic request flow for the current FastAPI starter service.

The current app includes:
- `GET /hello`
- `GET /health`
- `POST /echo`

The main goal of this file is to show how a request moves through the service from client request to JSON response.

---

## Example flow: `GET /hello`

```text
Client
  ↓
GET /hello
  ↓
FastAPI router receives request
  ↓
hello() endpoint runs
  ↓
build_hello_message()
  ↓
JSON response returned to client
```

---

## Example flow: `GET /health`

```text
Client
  ↓
GET /health
  ↓
FastAPI router receives request
  ↓
health() endpoint runs
  ↓
build_health_status()
  ↓
JSON response returned to client
```

---

## Example flow: `POST /echo`

```text
Client
  ↓
POST /echo
  ↓
FastAPI router receives request
  ↓
Pydantic validates request body
  ↓
echo() endpoint runs
  ↓
build_echo_response(message)
  ↓
JSON response returned to client
```

---

## Why this matters
This diagram shows the current service structure in a simple way:
- the router receives the request
- the endpoint handles the request
- helper logic builds the response
- FastAPI returns JSON to the client

This is useful for understanding and explaining:
- route structure
- request/response flow
- separation of endpoint and helper logic
- how the service could later grow into a more realistic ML API

---

## Next steps
Possible future extensions:
- add explicit response models
- add structured logging at each step
- add exception handling flow
- add request IDs
- add model-serving endpoints
