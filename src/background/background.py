import asyncio
import os.path
import traceback

from sqlalchemy import select

from src.db.session import AsyncSessionLocal
from src.kafka import kafka_consumer
from src.s3.client import get_s3_client
from src.utils.config import get_settings
from src.utils.logger import get_logger
from src.video.models import Video

logger = get_logger(__name__)
settings = get_settings()


class S3UploadWorker:
    """Background worker that uploads videos to S3."""

    def __init__(self, bucket: str):
        self.bucket = bucket
        self.kafka_consumer = kafka_consumer

    async def start(self):
        """Consume messages from Kafka and upload files to S3."""
        await self.kafka_consumer.start()
        try:
            async for msg in self.kafka_consumer.consumer:
                try:
                    payload = msg.value
                    video_id = payload.get("id")
                    local_path = payload.get("path")
                    if not os.path.exists(local_path):
                        continue

                    async with AsyncSessionLocal() as db:
                        stmt = select(Video).filter(Video.id == video_id)
                        result = await db.execute(stmt)
                        video = result.scalar_one_or_none()
                        if not video:
                            continue

                        key = f"{video.user_id}/{video_id}.mp4"

                        async with get_s3_client() as s3:
                            await s3.upload_file(
                                Filename=local_path, Bucket=self.bucket, Key=key
                            )
                        s3_url = f"{settings.S3_BASEURL}/{self.bucket}/{key}"
                        logger.info(f"Video {video_id} upload to {s3_url}")

                        video.s3_url = s3_url
                        video.key = key
                        await db.commit()
                    os.remove(local_path)
                except Exception as e:
                    logger.error(f"Error while upload video to s3: {e}")
                    print(traceback.format_exc())
                except asyncio.CancelledError:
                    logger.info("S3UploaderWorker has been cancel")
                    break
        except Exception as e:
            logger.error(f"Background worker except: {e}")
        finally:
            await self.kafka_consumer.stop()
