"""
app.py
-------
Main FastAPI application for the AI Router.

Endpoints
---------
GET  /            → {"status": "running"}
GET  /health      → server + model status
POST /predict     → full prediction + LLM answer
POST /route       → routing prediction only (no LLM call)

Swagger UI → /api/docs
ReDoc      → /api/redoc
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ai_router")


# ── Pydantic schemas ───────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2048, example="Install nginx on Ubuntu")


class PredictResponse(BaseModel):
    route:      str   = Field(..., example="LOCAL")
    confidence: float = Field(..., example=0.97)
    intent:     str   = Field(..., example="linux_install")
    complexity: float = Field(..., example=0.17)
    answer:     str   = Field(..., example="sudo apt install nginx")
    latency_ms: float = Field(..., example=1423.5)


class RouteResponse(BaseModel):
    route:      str
    confidence: float
    intent:     str
    complexity: float
    latency_ms: float


class HealthResponse(BaseModel):
    status:      str
    model:       str
    local_llm:   str
    cloud_llm:   str
    device:      str


# ── Lifespan: warm up all services once at startup ─────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model and initialise services before accepting requests."""
    logger.info("🚀 AI Router starting up …")
    t0 = time.perf_counter()

    # Import here so the model loads during lifespan, not at import time
    from initialize_model import initialize_models
    from predictor import Predictor
    from gemma import Gemma
    from fireworks import Fireworks

    app.state.predictor = Predictor()        # warms up the model singleton
    app.state.gemma     = Gemma()
    app.state.fireworks = Fireworks()
    app.state.model_info = initialize_models()

    elapsed = (time.perf_counter() - t0) * 1000
    logger.info("✅ All services ready in %.0f ms", elapsed)
    yield
    logger.info("👋 AI Router shutting down")


# ── FastAPI app ────────────────────────────────────────────────────────────

app = FastAPI(
    title       = "AI Router API",
    description = (
        "Intelligent routing between **Local LLM** (Gemma 3 via Ollama) and "
        "**Cloud LLM** (Llama 3.1 via Fireworks AI) using a fine-tuned "
        "DistilBERT multi-task router."
    ),
    version     = "1.0.0",
    docs_url    = "/api/docs",
    redoc_url   = "/api/redoc",
    lifespan    = lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Timing middleware ──────────────────────────────────────────────────────
@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start    = time.perf_counter()
    response = await call_next(request)
    elapsed  = (time.perf_counter() - start) * 1000
    response.headers["X-Response-Time-Ms"] = f"{elapsed:.1f}"
    logger.debug("%s %s → %.1f ms", request.method, request.url.path, elapsed)
    return response


# ── Routes ─────────────────────────────────────────────────────────────────

@app.get("/", tags=["Status"], summary="Root ping")
def root():
    """Quick liveness check."""
    return {"status": "running", "service": "AI Router API", "version": "1.0.0"}


@app.get("/health", response_model=HealthResponse, tags=["Status"], summary="Health check")
def health(request: Request):
    """Returns server and model status information."""
    info = request.app.state.model_info
    return HealthResponse(
        status    = "healthy",
        model     = "MultiTaskRouter (distilbert-base-uncased)",
        local_llm = "Gemma 3 via Ollama (localhost:11434)",
        cloud_llm = "Llama 3.1-8B via Fireworks AI",
        device    = str(info.device),
    )


@app.post(
    "/predict",
    response_model = PredictResponse,
    tags           = ["Prediction"],
    summary        = "Full prediction — route + answer",
)
def predict(body: QueryRequest, request: Request):
    """
    Classify the query, select the appropriate LLM, generate an answer,
    and return everything in a single response.
    """
    t0 = time.perf_counter()

    predictor = request.app.state.predictor
    gemma     = request.app.state.gemma
    fireworks = request.app.state.fireworks

    try:
        # 1. Routing decision
        routing = predictor.predict(body.query)

        # 2. LLM generation
        if routing["route"] == "LOCAL":
            answer = gemma.generate(body.query)
        else:
            answer = fireworks.generate(body.query)

        latency_ms = (time.perf_counter() - t0) * 1000
        return PredictResponse(
            route      = routing["route"],
            confidence = routing["confidence"],
            intent     = routing["intent"],
            complexity = routing["complexity"],
            answer     = answer,
            latency_ms = round(latency_ms, 1),
        )

    except Exception as exc:
        logger.error("Prediction error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post(
    "/route",
    response_model = RouteResponse,
    tags           = ["Prediction"],
    summary        = "Route-only — no LLM call",
)
def route_only(body: QueryRequest, request: Request):
    """
    Return the routing decision (route, intent, confidence, complexity)
    without calling any LLM. Useful for testing the router model alone.
    """
    t0 = time.perf_counter()

    predictor = request.app.state.predictor

    try:
        routing    = predictor.predict(body.query)
        latency_ms = (time.perf_counter() - t0) * 1000
        return RouteResponse(
            route      = routing["route"],
            confidence = routing["confidence"],
            intent     = routing["intent"],
            complexity = routing["complexity"],
            latency_ms = round(latency_ms, 1),
        )
    except Exception as exc:
        logger.error("Route error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc