import logging
from fastapi import FastAPI, HTTPException
from app.schemas import EchoRequest, EchoResponse

app = FastAPI()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def build_hello_message() -> dict[str, str]:
    return {"message": "hello"}

def build_health_message() -> dict[str, str]:
    return {"status": "ok"}

def build_echo_response(message: str) -> EchoResponse:
    return EchoResponse(message=message)

@app.get("/hello")
def hello() -> dict[str, str]:
    return build_hello_message()


@app.get("/health")
def health() -> dict[str, str]:
    return build_health_message()
    
@app.post("/echo", response_model=EchoResponse)
def echo(request: EchoRequest) -> EchoResponse:
    logger.info("request received endpoint=echo")

    if not request.message.strip():
        logger.error("request_failed endpoint=echo reason=empty_message")
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    response = build_echo_response(request.message)
    logger.info("request_processed_successfully endpoint=echo")
    return response





