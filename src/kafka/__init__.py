from src.kafka.consumer import KafkaConsumer
from src.kafka.producer import KafkaProducer
from src.utils.config import get_settings

settings = get_settings()

# Init kafka custom class
kafka_producer = KafkaProducer(settings.kafka_servers)
kafka_consumer = KafkaConsumer(settings.kafka_servers, topics="videos")
