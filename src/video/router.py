import json
import os
import tempfile

import aiofiles
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    status,
    UploadFile,
)
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette.templating import Jinja2Templates

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.db.session import get_db
from src.kafka import kafka_producer
from src.s3.client import get_s3_client
from src.utils.config import get_settings
from src.utils.logger import get_logger
from src.utils.mime_type import is_mp4
from src.video import schemas
from src.video.models import Video

settings = get_settings()
templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/video", tags=["Video"])
logger = get_logger(__name__)


@router.post(
    "/upload",
    response_model=schemas.UploadResponse,
    summary="Upload video",
    description="Upload MP4 file and create asynchronous task",
    responses={
        200: {"description": "Video accepted for processing"},
        400: {"description": "File is not a valid mp4"},
    },
)
async def upload_video(
    name: str = Form(..., description="Video title"),
    description: str = Form(..., description="Video description"),
    file: UploadFile = File(..., description="MP4 file"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save uploaded video and enqueue background upload task."""
    # Download file and create message in kafka
    if file.content_type != "video/mp4":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="mp4 files only"
        )

    # Store file in system temporary directory
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp_path = tmp.name

    size = 0
    async with aiofiles.open(tmp_path, "wb") as out_file:
        while True:
            chunk = await file.read(1024 * 1024 * 2)
            if not chunk:
                break
            size += len(chunk)
            if size > settings.video_max_size:
                await out_file.close()
                os.remove(tmp_path)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File too large",
                )
            await out_file.write(chunk)

    if not is_mp4(tmp_path):
        os.remove(tmp_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="mp4 files only"
        )

    new_video = Video(
        name=name,
        description=description,
        user_id=current_user.id,
    )
    db.add(new_video)
    await db.flush()

    payload = {
        "id": new_video.id,
        "name": name,
        "description": description,
        "path": tmp_path,
    }

    await kafka_producer.producer.send(
        "videos", value=json.dumps(payload).encode("utf-8")
    )
    await kafka_producer.producer.flush()

    return {"id": new_video.id, "status": "accepted"}


@router.get(
    "/{video_id}/player",
    summary="Return video player",
    responses={
        200: {"description": "HTML page with video player"},
        404: {"description": "Video not found"},
    },
)
async def get_video_player(
    request: Request, video_id: int, db: AsyncSession = Depends(get_db)
):
    """Return simple HTML player for the requested video."""
    # Get simple html with video player
    stmt = select(Video).filter(Video.id == video_id)
    try:
        result = await db.execute(stmt)
        video = result.scalar_one()
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )

    async with get_s3_client() as s3:
        url = await s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": settings.s3_bucket, "Key": video.key},
            ExpiresIn=3600,
        )

    return templates.TemplateResponse("player.html", {"request": request, "url": url})


@router.get(
    "/{video_id}/status",
    response_model=schemas.UploadResponse,
    summary="Get video upload status",
    description="Check if video has been uploaded to S3",
    responses={
        200: {"description": "Current upload status"},
        404: {"description": "Video not found"},
    },
)
async def get_video_upload_status(video_id: int, db: AsyncSession = Depends(get_db)):
    """Return upload status for video."""
    # Get video upload status
    stmt = select(Video).filter(Video.id == video_id)
    try:
        result = await db.execute(stmt)
        video = result.scalar_one()
        return {
            "id": video.id,
            "status": "accepted" if not video.s3_url else "uploaded",
        }
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )


@router.delete(
    "/{video_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete video",
    responses={
        204: {"description": "Video deleted"},
        403: {"description": "Access denied"},
        404: {"description": "Video not found"},
    },
)
async def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove video from DB and S3 if it exists."""
    # Delete video from db and S3
    stmt = select(Video).filter(Video.id == video_id)
    try:
        result = await db.execute(stmt)
        video = result.scalar_one()
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not found"
        )

    if video.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    await db.delete(video)

    if video.key:
        async with get_s3_client() as s3:
            await s3.delete_object(Bucket=settings.s3_bucket, Key=video.key)

    return {"status": "success"}
