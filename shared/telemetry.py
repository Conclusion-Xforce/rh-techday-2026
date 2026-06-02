import logging
import os

# Must be set before any OTel/metric exporter is initialized
os.environ.setdefault("OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE", "delta")
os.environ.setdefault("TRACELOOP_TELEMETRY", "false")

from opentelemetry import metrics, trace
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger(__name__)

# Cluster-internal BindPlane node agent (HTTP OTLP, no auth required)
_DEFAULT_OTLP_ENDPOINT = "http://bindplane-node-agent.bindplane-agent.svc.cluster.local:4318"


def _parse_headers(headers_str: str) -> dict:
    result = {}
    for pair in headers_str.split(","):
        if "=" in pair:
            k, v = pair.split("=", 1)
            result[k.strip()] = v.strip()
    return result


def _setup_metric_provider(endpoint: str, headers: dict, resource: Resource) -> None:
    """Configure a MeterProvider with OTLP HTTP export.

    This is required for gen_ai.client.token.usage histograms (and any other
    OTEL metrics) to reach Dynatrace.  The delta temporality preference must
    already be set in the environment before this function is called.
    """
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

    exporter = OTLPMetricExporter(
        endpoint=f"{endpoint}/v1/metrics",
        headers=headers or {},
    )
    reader = PeriodicExportingMetricReader(exporter, export_interval_millis=30_000)
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)


def init_telemetry() -> trace.Tracer:
    service_name = os.environ.get("OTEL_SERVICE_NAME", "unknown-service")
    exporter_mode = os.environ.get("OTEL_EXPORTER", "otlp").lower()
    resource = Resource.create({"service.name": service_name})

    if exporter_mode == "console":
        # Local dev: print spans to stdout, skip Traceloop and metric export
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

        provider = TracerProvider(resource=resource)
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(provider)
    else:
        endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", _DEFAULT_OTLP_ENDPOINT)
        headers_str = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "")
        headers = _parse_headers(headers_str) if headers_str else {}

        # ── Metric pipeline ─────────────────────────────────────────────────
        # Must be set up before trace provider so the MeterProvider is ready
        # when Traceloop/OpenAI instrumentation emits token-usage metrics.
        _setup_metric_provider(endpoint, headers, resource)

        # ── Trace pipeline via Traceloop ─────────────────────────────────────
        # Traceloop owns the TracerProvider and adds @workflow / association
        # property support on top of standard OTel.
        try:
            from traceloop.sdk import Traceloop

            Traceloop.init(
                app_name=service_name,
                api_endpoint=endpoint,
                headers=headers or None,
                disable_batch=False,
                should_enrich_metrics=True,
                resource_attributes={"service.name": service_name},
            )
        except Exception:
            logger.exception(
                "Traceloop.init() failed — falling back to plain OTLP trace export. "
                "@workflow spans will be missing but standard OTel spans will still export."
            )
            # Fallback: set up a plain OTLP trace provider so spans still export
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            provider = TracerProvider(resource=resource)
            provider.add_span_processor(
                BatchSpanProcessor(
                    OTLPSpanExporter(
                        endpoint=f"{endpoint}/v1/traces",
                        headers=headers or {},
                    )
                )
            )
            trace.set_tracer_provider(provider)

    # ── Auto-instrumentors ───────────────────────────────────────────────────
    # Each attaches to whatever TracerProvider is now globally registered.

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

    # OpenAI instrumentation: emits gen_ai.* span attributes and
    # gen_ai.client.token.usage metrics that Dynatrace AI Observability needs.
    # Called explicitly here so it works even when Traceloop.init() fails.
    try:
        from opentelemetry.instrumentation.openai import OpenAIInstrumentor
        OpenAIInstrumentor().instrument()
    except ImportError:
        logger.warning(
            "opentelemetry-instrumentation-openai not installed — "
            "gen_ai.* span attributes will be missing. "
            "Add it to requirements.txt to enable AI Observability metrics."
        )

    return trace.get_tracer(service_name)
