import asyncio
import redis
from faststream import FastStream
from faststream.confluent import KafkaBroker, KafkaMessage
# from vllm import LLM, SamplingParams

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

# Setup
redis_client = redis.Redis(password='yourpassword')
# llm = LLM(model="facebook/opt-125m")
# sampling_params = SamplingParams(temperature=0.8, top_p=0.95)


async def stream_tokens(input: str):
    text = "this is a response"

    for t in text.split(" "):
        await asyncio.sleep(0.2)
        yield t + ' '


@broker.subscriber("chat.incoming", auto_offset_reset="earliest")
async def process_request(
    body: str,
    msg: KafkaMessage,
):
    # vLLM generates a generator object
    request_id = msg.headers["correlation_id"]

    async for output in stream_tokens(body):
        # Get the newly generated token
        new_text = output

        # Publish to Redis Channel
        # Channel Name: "stream:<request_id>"
        redis_client.publish(f"stream:{request_id}", new_text)

    # Signal completion
    redis_client.publish(f"stream:{request_id}", "[DONE]")
