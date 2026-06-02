import os

# Must be set before any OTel/metric exporter is initialized
os.environ.setdefault("OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE", "delta")
os.environ.setdefault("TRACELOOP_TELEMETRY", "false")

from opentelemetry import trace

# Cluster-internal BindPlane node agent (HTTP OTLP, no auth required)
_DEFAULT_OTLP_ENDPOINT = "http://bindplane-node-agent.bindplane-agent.svc.cluster.local:4318"


def init_telemetry() -> trace.Tracer:
    service_name = os.environ.get("OTEL_SERVICE_NAME", "unknown-service")
    exporter_mode = os.environ.get("OTEL_EXPORTER", "otlp").lower()

    if exporter_mode == "console":
        # Local dev: print spans to stdout, skip Traceloop
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(provider)
    else:
        # Production: Traceloop owns the TracerProvider + OpenAI auto-instrumentation.
        # It detects the ProxyTracerProvider and registers its own provider globally,
        # which the auto-instrumentors below will then pick up.
        from traceloop.sdk import Traceloop

        endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", _DEFAULT_OTLP_ENDPOINT)
        headers_str = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "")
        headers = {}
        if headers_str:
            for pair in headers_str.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    headers[k.strip()] = v.strip()

        Traceloop.init(
            app_name=service_name,
            api_endpoint=endpoint,
            headers=headers or None,
            disable_batch=False,
            should_enrich_metrics=True,
            resource_attributes={"service.name": service_name},
        )

    # Auto-instrumentors attach to whatever TracerProvider is now globally registered
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

    return trace.get_tracer(service_name)
