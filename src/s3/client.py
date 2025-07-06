import aioboto3
from botocore.config import Config

from src.utils.config import get_settings

settings = get_settings()

config = Config(
    region_name=settings.s3_region,
    signature_version="s3v4",
    s3={'addressing_style': 'path'}
)


def get_s3_client() -> aioboto3.Session.client:
    """
    Generate boto3 client for use S3
    """
    session = aioboto3.Session()
    return session.client(
        service_name="s3",
        endpoint_url=settings.s3_endpoint or settings.s3_baseurl,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        config=config
    )
