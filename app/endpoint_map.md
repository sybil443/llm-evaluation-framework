# Endpoint Map

## Goal
Document the current FastAPI endpoints and show the intended direction for future API structure.

## Current endpoints

### `GET /hello`
Returns a simple greeting response.

#### Purpose
Starter endpoint used to verify the service is running and the request/response flow works.

#### Response
```json
{
  "message": "hello"
}

### `GET /health`
Returns a simple service health response.

#### Purpose
Lightweight health check endpoint.

#### Response
```json
{
  "status": "ok"
}

### `POST /echo`
Accepts a request body containing a message and returns that message in the response.

#### Purpose
Starter endpoint for practicing:
- request validation
- response models
- structured logging
- basic error handling

#### Response
```json
{
  "message": "hello"
}