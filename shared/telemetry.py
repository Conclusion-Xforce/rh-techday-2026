import os

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource


def init_telemetry() -> trace.Tracer:
    service_name = os.environ.get("OTEL_SERVICE_NAME", "unknown-service")
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    exporter_mode = os.environ.get("OTEL_EXPORTER", "otlp").lower()
    if exporter_mode == "console":
        from opentelemetry.sdk.trace.export import (
            SimpleSpanProcessor,
            ConsoleSpanExporter,
        )

        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    else:
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )

        endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
        headers_str = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "")
        headers = {}
        if headers_str:
            for pair in headers_str.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    headers[k.strip()] = v.strip()

        exporter = OTLPSpanExporter(
            endpoint=f"{endpoint}/v1/traces" if endpoint else None,
            headers=headers or None,
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)

    # Auto-instrumentors — each is conditional on the package being installed
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor().instrument()
    except ImportError:
        pass

    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
    except ImportError:
        pass

    try:
        from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

        Psycopg2Instrumentor().instrument()
    except ImportError:
        pass

    # Traceloop (openllmetry) for LLM span capture
    try:
        from traceloop.sdk import Traceloop

        Traceloop.init(
            app_name=service_name,
            disable_batch=exporter_mode == "console",
        )
    except ImportError:
        pass

    return trace.get_tracer(service_name)
