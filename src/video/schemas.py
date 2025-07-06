from pydantic import BaseModel, ConfigDict, constr, Field


class Upload(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )
    name: constr(min_length=5, max_length=64) = Field(
        ..., description="Video title"
    )
    description: constr(max_length=1024) = Field(
        ..., description="Optional description of the video"
    )


class Status(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )
    id: int = Field(..., description="Video identifier")


class UploadResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )
    id: int = Field(..., description="Video identifier")
    status: str = Field(..., description="Current upload status")
