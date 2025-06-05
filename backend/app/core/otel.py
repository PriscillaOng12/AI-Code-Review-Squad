"""OpenTelemetry configuration."""

from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from .config import settings
from .database import engine


def configure_tracing(app) -> None:
    """Configure the OpenTelemetry SDK and instrument FastAPI, SQLAlchemy and Celery."""
    resource = Resource.create({"service.name": settings.otel_service_name})
    provider = TracerProvider(resource=resource)
    if settings.otel_exporter_otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        # Instrument libraries
        FastAPIInstrumentor().instrument_app(app)
        SQLAlchemyInstrumentor().instrument(engine=engine)
        CeleryInstrumentor().instrument()