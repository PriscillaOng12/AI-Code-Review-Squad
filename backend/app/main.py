"""Entry point for the FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from .core.config import settings
from .core.logging import configure_logging
from .core.otel import configure_tracing
from .api.routes import health, reviews, findings, webhook_github, exports


app = FastAPI(title="ai-code-review-squad API", openapi_url="/openapi.json")

# Configure logging
configure_logging()

# Configure tracing
configure_tracing(app)

# CORS
origins = [orig.strip() for orig in settings.allowed_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Prometheus metrics
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP request latency", ["endpoint"])


@app.middleware("http")
async def metrics_middleware(request, call_next):
    endpoint = request.url.path
    REQUEST_COUNT.labels(method=request.method, endpoint=endpoint).inc()
    with REQUEST_LATENCY.labels(endpoint=endpoint).time():
        response = await call_next(request)
    return response


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Include routers
app.include_router(health.router, prefix="/api")
app.include_router(webhook_github.router, prefix="/api/webhooks")
app.include_router(reviews.router, prefix="/api")
app.include_router(findings.router, prefix="/api")
app.include_router(exports.router, prefix="/api/exports")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.api_port)