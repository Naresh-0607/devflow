from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.config import settings
from app.deps import CurrentUser, DbSession
from app.models import RefreshToken, User, utcnow
from app.schemas import (
    AuthResponse,
    RefreshRequest,
    TokenPair,
    UserCreate,
    UserLogin,
    UserOut,
)
from app.security import (
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(db: DbSession, user: User) -> TokenPair:
    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    return TokenPair(access_token=access, refresh_token=refresh)


async def _store_refresh_token(db: DbSession, user: User, token: str) -> None:
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.refresh_token_expire_days),
        )
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: DbSession) -> AuthResponse:
    existing = (
        await db.execute(select(User).where(User.email == payload.email.lower()))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password))
    db.add(user)
    await db.flush()

    tokens = _issue_tokens(db, user)
    await _store_refresh_token(db, user, tokens.refresh_token)
    await db.commit()
    await db.refresh(user)

    return AuthResponse(user=UserOut.model_validate(user), tokens=tokens)


@router.post("/login", response_model=AuthResponse)
async def login(payload: UserLogin, db: DbSession) -> AuthResponse:
    user = (
        await db.execute(select(User).where(User.email == payload.email.lower()))
    ).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    tokens = _issue_tokens(db, user)
    await _store_refresh_token(db, user, tokens.refresh_token)
    await db.commit()
    return AuthResponse(user=UserOut.model_validate(user), tokens=tokens)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: DbSession) -> TokenPair:
    jwt_payload = decode_token(payload.refresh_token, REFRESH_TOKEN_TYPE)
    if jwt_payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    token_hash = hash_refresh_token(payload.refresh_token)
    stored = (
        await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    ).scalar_one_or_none()
    now = utcnow()
    expires_at = stored.expires_at if stored else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if stored is None or stored.revoked_at is not None or expires_at <= now:
        raise HTTPException(status_code=401, detail="Refresh token is no longer valid")

    stored.revoked_at = now  # rotation
    user = await db.get(User, stored.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    tokens = _issue_tokens(db, user)
    await _store_refresh_token(db, user, tokens.refresh_token)
    await db.commit()
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest, db: DbSession) -> Response:
    stored = (
        await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_refresh_token(payload.refresh_token)
            )
        )
    ).scalar_one_or_none()
    if stored is not None and stored.revoked_at is None:
        stored.revoked_at = utcnow()
        await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
