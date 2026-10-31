import logging
from fastapi import FastAPI, HTTPException
from app.routes.evaluations import router

app = FastAPI(
    title="LLM Evaluation Framework: Baseline vs. Challenger Comparison", version="1.0.0",
    description="Local offline comparison of supplied model outputs. No model is called.",
)
app.include_router(router, prefix="/v1")
logging.basicConfig(level=logging.INFO)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}