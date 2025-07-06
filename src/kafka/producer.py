from aiokafka import AIOKafkaProducer


class KafkaProducer:
    def __init__(self, bootstrap_servers):
        self.bootstrap_servers = bootstrap_servers
        self._producer = None

    async def start(self):
        if not self.producer:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers
            )
        await self.producer.start()

    async def stop(self):
        await self.producer.stop()

    @property
    def producer(self):
        return self._producer
