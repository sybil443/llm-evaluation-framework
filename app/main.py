import logging
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class EchoRequest(BaseModel):
    message: str

def build_hello_message() -> dict[str, str]:
    return {"message": "hello"}

def build_echo_message(message:str) -> dict[str, str]:
    return {"message": message}

@app.get("/hello")
def hello() -> dict[str, str]:
    return build_hello_message()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
    
@app.post("/echo")
def echo(request: EchoRequest) -> dict[str, str]:
    logger.info("request received endpoint = echo")

    response = build_echo_message(request.message)
    logger.info("request_processed_successfully endpoint = echo")
    return response





