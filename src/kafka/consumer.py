import json

from aiokafka import AIOKafkaConsumer


class KafkaConsumer:
    def __init__(self, bootstrap_servers, topics, group_id="async-test-group"):
        self.bootstrap_servers = bootstrap_servers
        self.topics = topics if isinstance(topics, list) else [topics]
        self.group_id = group_id
        self._consumer = None

    async def start(self):
        if not self._consumer:
            self._consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode("utf-8"))
            )
        await self._consumer.start()

    async def stop(self):
        await self._consumer.stop()

    @property
    def consumer(self) -> AIOKafkaConsumer:
        return self._consumer
