from contextlib import asynccontextmanager
import uuid
from fastapi import FastAPI
from faststream.confluent import KafkaBroker
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.kafka import KafkaInstrumentor
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import redis.asyncio as redis  # Async Redis client
from faststream.kafka.opentelemetry import KafkaTelemetryMiddleware
from src.settings import settings
from src.telemetry import setup_telemetry


print(settings.kafka.bootstrap_servers)

tracer_provider = setup_telemetry("chat-gateway")
broker = KafkaBroker(
    settings.kafka.bootstrap_servers,
    middlewares=[KafkaTelemetryMiddleware(tracer_provider=tracer_provider)],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.start()
    yield
    await broker.stop()


app = FastAPI(lifespan=lifespan)


FastAPIInstrumentor.instrument_app(app)
KafkaInstrumentor().instrument()


class MSG(BaseModel):
    prompt: str


@app.post("/chat")
async def chat(msg: MSG):
    correlation_id = str(uuid.uuid4())
    await broker.publish(
        msg.prompt, topic="chat.incoming", correlation_id=correlation_id
    )
    return {
        "status": "sent",
        "correlation_id": correlation_id,
    }


async def stream_generator(request_id: str):
    r = redis.Redis(
        host=settings.redis.host,
        port=settings.redis.port,
        password=settings.redis.password,
        decode_responses=True,
    )
    pubsub = r.pubsub()
    await pubsub.subscribe(f"stream:{request_id}")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = message["data"]
                if data == "[DONE]":
                    break
                # SSE format: "data: <content>\n\n"
                yield f"data: {data}\n\n"
    finally:
        await r.close()


@app.get("/stream/{request_id}")
async def stream_response(request_id: str):
    return StreamingResponse(
        stream_generator(request_id), media_type="text/event-stream"
    )
