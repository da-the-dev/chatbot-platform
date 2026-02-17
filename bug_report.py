from faststream import FastStream
from faststream.confluent import KafkaBroker, KafkaMessage
from faststream.kafka.opentelemetry import KafkaTelemetryMiddleware
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


# Setup tracing
resource = Resource.create({"service.name": "inference-worker"})
tracer_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider)
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)


# Broker and app
broker = KafkaBroker(
    "localhost:9092",
    middlewares=[KafkaTelemetryMiddleware(tracer_provider=tracer_provider)],
)
app = FastStream(broker)


# Basic subscriber
@broker.subscriber("chat.incoming", auto_offset_reset="earliest")
async def process_request(
    body: str,
    msg: KafkaMessage,
):
    print(body, msg.correlation_id)
