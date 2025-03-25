from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from confluent_kafka import Producer, Consumer
from app.core.config import settings

# Initialize MongoDB Connection
mongo_client = AsyncIOMotorClient(f"mongodb://{settings.MONGO_HOST}:{settings.MONGO_PORT}/")
mongo_db = mongo_client[settings.MONGO_DB]

# Initialize Redis Connection
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

# Initialize Kafka Producer
producer_conf = {"bootstrap.servers": f"localhost:{settings.KAFKA_PORT}"}
kafka_producer = Producer(producer_conf)

# # Initialize Kafka Consumer
# consumer_conf = {
#     "bootstrap.servers": f"localhost:{settings.KAFKA_PORT}",
#     "group.id": settings.KAFKA_GROUP_ID,
#     "auto.offset.reset": "earliest",
# }
# kafka_consumer = Consumer(consumer_conf)
# kafka_consumer.subscribe([settings.KAFKA_TOPIC])
