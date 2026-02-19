# telemetry.py
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


def setup_telemetry(service_name: str):
    # 1. Define the Service Name (appears in Jaeger)
    resource = Resource.create({'service.name': service_name})

    # 2. Setup the Provider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    # 3. Setup the Exporter (Sends data to Jaeger/Tempo)
    # Assumes Jaeger is running on localhost:4317
    otlp_exporter = OTLPSpanExporter(endpoint='http://localhost:4317', insecure=True)

    # 4. Add the Processor (Batches spans for performance)
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    return tracer_provider
