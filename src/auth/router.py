from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.auth import schemas
from src.auth.models import User
from src.auth.security import create_access_token, get_password_hash, verify_password
from src.db.session import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=schemas.AuthResponse,
    summary="Register user",
    description="Create a new user account",
    responses={
        200: {"description": "User successfully created"},
        400: {"description": "Login already exists"},
    },
)
async def register_user(
        data: schemas.AuthRegister,
        db: AsyncSession = Depends(get_db)
):
    # Register new user
    existing = (await db.execute(
        select(User).where(User.login == data.login)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Login already exists"
        )

    new_user = User(
        login=data.login,
        hashed_password=get_password_hash(data.password)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post(
    "/login",
    response_model=schemas.UserLoginResponse,
    summary="Login user",
    description="Authenticate user and return JWT",
    responses={
        200: {"description": "Successful authentication"},
        404: {"description": "Incorrect login or password"},
    },
)
async def login_user(
        data: schemas.UserLogin,
        db: AsyncSession = Depends(get_db)
):
    # Generate JWT token for upload video
    q = await db.execute(
        select(User).where(User.login == data.login)
    )
    user = q.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incorrect login or password",
        )

    token = create_access_token(
        {"user_id": user.id, "login": user.login}
    )
    return {"access_token": token, "token_type": "bearer"}
