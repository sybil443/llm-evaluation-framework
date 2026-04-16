# API Contract Note

## Purpose
This note defines the current API contract for the FastAPI starter service, with focus on the Week 2 ML engineer artifact:
- input validation
- request/response structure
- endpoint behavior

The main endpoint documented here is:

- `POST /echo`

---

## Endpoint Summary

### `POST /echo`
Accepts a JSON request body containing a message string and returns that message in the response.

### Purpose
This endpoint is a simple starter example for practicing:
- request validation
- route handling
- helper-function separation
- structured logging
- API documentation

---

## Request Contract

### Method
`POST`

### Path
`/echo`

### Content Type
`application/json`

### Request Body Schema

```json
{
  "message": "string"
}
```

### Field Definitions
- `message`
    - required
    - type: string

## Response Contract
### Success Response

Status: `200 OK`

### Response Body Schema
```json
{
  "message": "string"
}
```
### Example Success Request
```json
{
  "message": "hello"
}
```
### Example Success Response
```json
{
  "message": "hello"
}
```
## Validation Rules

The request body is validated with a Pydantic model.

### Current validation
- `message` must be present
- `message` must be a string
### Invalid examples
### Missing field
```json
{}
```

### Wrong type
```json
{
  "message": 123
}
```

In these cases, FastAPI returns a validation error response automatically.

## Processing Flow

Current logical flow:
```
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
JSON response returned
```

## Logging Behavior

The endpoint currently logs:

- request received
- request processed successfully

This provides a small example of structured logging within the request flow.

## Design Notes
### Why use a request model?

A Pydantic request model makes validation explicit and keeps endpoint input predictable.

### Why return the same message?

The `echo` behavior is intentionally simple so the focus stays on:

- API contract clarity
- validation
- logging
- service structure

### Why separate helper logic?

Using a helper function keeps the route layer lightweight and makes later extension easier.


## Future Extensions

Possible next steps:

- add response models
- add explicit error-handling logs
- validate message length or content
- add request IDs
- add latency logging
- add prediction-style endpoints for ML serving