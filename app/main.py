import logging
from fastapi import FastAPI, HTTPException
from app.routes.evaluations import router
from app.schemas import EchoRequest, EchoResponse

app = FastAPI(
    title="LLM / Model Evaluation Framework", version="1.0.0",
    description="Local offline comparison of supplied model outputs. No model is called.",
)
app.include_router(router, prefix="/v1")
logging.basicConfig(level=logging.INFO)


@app.get("/hello")
def hello() -> dict[str, str]:
    return {"message": "hello"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/echo", response_model=EchoResponse)
def echo(request: EchoRequest) -> EchoResponse:
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    return EchoResponse(message=request.message)