import asyncio
from contextlib import asynccontextmanager
import redis
from faststream import ContextRepo, FastStream, Context
from faststream.confluent import KafkaBroker, KafkaMessage
from faststream.kafka.opentelemetry import KafkaTelemetryMiddleware
from opentelemetry.instrumentation.kafka import KafkaInstrumentor
from opentelemetry import trace
from telemetry import setup_telemetry


broker = KafkaBroker(
    "localhost:9092",
    middlewares=[
        KafkaTelemetryMiddleware(tracer_provider=setup_telemetry("inference-worker"))
    ],
)


@asynccontextmanager
async def lifespan(context: ContextRepo):
    KafkaInstrumentor().instrument()

    redis_client = redis.Redis(password="yourpassword")
    context.set_global("redis_client", redis_client)

    yield

    redis_client.close()


app = FastStream(broker, lifespan=lifespan)
tracer = trace.get_tracer(__name__)


async def stream_tokens(input: str):
    text = "this is a response"

    for t in text.split(" "):
        await asyncio.sleep(0.5)
        yield t + " "


@broker.subscriber("chat.incoming", auto_offset_reset="earliest")
async def process_request(
    body: str,
    msg: KafkaMessage,
    redis_client: redis.Redis = Context(),
):
    # vLLM generates a generator object
    request_id = msg.headers["correlation_id"]

    with tracer.start_span("vllm_generation"):
        async for token in stream_tokens(body):
            # with tracer.start_span('redis_publish_'):
            redis_client.publish(f"stream:{request_id}", token)

    with tracer.start_span("redis_publish_fin"):
        redis_client.publish(f"stream:{request_id}", "[DONE]")
