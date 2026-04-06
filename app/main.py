from fastapi import FastAPI

app = FastAPI()


def build_hello_message() -> dict[str, str]:
    return {"message": "hello"}


@app.get("/hello")
def hello() -> dict[str, str]:
    return build_hello_message()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}