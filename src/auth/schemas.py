from datetime import datetime

from pydantic import BaseModel, ConfigDict, constr, Field


class AuthRegister(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    login: constr(min_length=3, max_length=50) = Field(
        ..., description="Unique user login"
    )
    password: constr(min_length=8) = Field(
        ..., description="Password with minimum length of 8 characters"
    )


class AuthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="User identifier")
    login: str = Field(..., description="User login")
    created_at: datetime = Field(..., description="Registration timestamp")


class UserLogin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    login: str = Field(..., description="User login")
    password: str = Field(..., description="User password")


class UserLoginResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(..., description="Token type, always 'bearer'")
