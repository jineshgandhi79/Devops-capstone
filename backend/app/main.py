import os
import time

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.routes import todos

APP_VERSION = "1.0.0"
ENVIRONMENT = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development"))

app = FastAPI(
    title="DevTrack Todo API",
    description="Todo management REST API — DevOps capstone project by Jinesh Gandhi",
    version=APP_VERSION,
)

# Prometheus metrics. Names are kept as devtrack_* so the existing
# Prometheus scrape config and Grafana dashboard work unchanged.
REQUEST_COUNT = Counter(
    "devtrack_http_requests_total",
    "Total count of HTTP requests processed by the API",
    ["method", "endpoint", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "devtrack_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
APP_INFO = Gauge("devtrack_app_info", "Application build and version metadata", ["app", "version"])
APP_INFO.labels(app="devtrack-todo-api", version=APP_VERSION).set(1)

# CORS is only needed for the Vite dev server; in Docker and Kubernetes the
# frontend calls the API on the same origin via /api.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def prometheus_request_middleware(request: Request, call_next):
    """Record request count and latency, labelled by route template to keep cardinality low."""
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    route = request.scope.get("route")
    endpoint = getattr(route, "path_format", None) or getattr(route, "path", None) or "unmatched"

    REQUEST_COUNT.labels(request.method, endpoint, str(response.status_code)).inc()
    REQUEST_LATENCY.labels(request.method, endpoint).observe(duration)
    return response


app.include_router(todos.router)


@app.get("/", tags=["General"])
def read_root():
    return {
        "message": "Welcome to DevTrack Todo API",
        "version": APP_VERSION,
        "docs_url": "/docs",
    }


@app.get("/health", tags=["Monitoring"])
def health_check():
    """Liveness probe: the process is up and serving HTTP."""
    return {"status": "healthy"}


@app.get("/ready", tags=["Monitoring"])
def readiness_check(db: Session = Depends(get_db)):
    """Readiness probe: the database is reachable, so traffic can be served."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "database": "unreachable"},
        )
    return {"status": "ready", "database": "connected"}


@app.get("/api/info", tags=["General"])
def app_info():
    """Build metadata shown in the frontend footer."""
    return {"app": "DevTrack Todo", "version": APP_VERSION, "environment": ENVIRONMENT}


@app.get("/metrics", tags=["Monitoring"])
def metrics():
    """Prometheus text exposition endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
