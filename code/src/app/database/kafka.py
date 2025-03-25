from confluent_kafka import Producer, Consumer
from app.core.config import settings

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