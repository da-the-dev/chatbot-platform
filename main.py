import asyncio
from faststream import FastStream
from faststream.confluent import KafkaBroker, KafkaMessage

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.subscriber("chat.incoming", auto_offset_reset="earliest")
async def handle(body: str, msg: KafkaMessage):
    pass
    # await broker.publish("Hi!", topic="another-topic")


# @broker.subscriber("another-topic", auto_offset_reset="earliest")
# async def handle_next(msg: str):
#     assert msg == "Hi!"


@app.after_startup
async def test():
    print("SENT")
    await broker.publish("hi", topic="chat.incoming")
