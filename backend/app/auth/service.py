from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Tuple

import jwt
from fastapi import HTTPException, status

from app.core.config import get_settings

from .repository import PostgresAuthRepository
from .schemas import LoginRequest, RefreshTokenRequest, SignupRequest, TokenResponse, UserResponse


class AuthService:
    def __init__(self, repository: PostgresAuthRepository | None = None) -> None:
        self.repository = repository or PostgresAuthRepository()
        self.secret_key = get_settings().jwt_secret_key

    async def signup(self, payload: SignupRequest) -> UserResponse:
        existing_user = await self.repository.get_user_by_email(str(payload.email))
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        password_hash = self._hash_password(payload.password)
        user = await self.repository.create_user(
            user_id=str(uuid.uuid4()),
            email=str(payload.email),
            full_name=payload.full_name,
            password_hash=password_hash,
        )
        return UserResponse(id=user.id, email=user.email, full_name=user.full_name)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        user = await self.repository.get_user_by_email(str(payload.email))
        if not user or not self._verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        access_token, refresh_token = self._generate_tokens(user.id)
        await self.repository.update_refresh_token(user.id, refresh_token)
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def refresh(self, payload: RefreshTokenRequest) -> TokenResponse:
        user = await self.repository.get_user_by_refresh_token(payload.refresh_token)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        access_token, refresh_token = self._generate_tokens(user.id)
        await self.repository.update_refresh_token(user.id, refresh_token)
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    def _generate_tokens(self, user_id: str) -> Tuple[str, str]:
        now = datetime.now(timezone.utc)
        access_payload = {
            "sub": user_id,
            "token_type": "access",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=15)).timestamp()),
        }
        refresh_payload = {
            "sub": user_id,
            "token_type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=7)).timestamp()),
        }
        access_token = jwt.encode(access_payload, self.secret_key, algorithm="HS256")
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm="HS256")
        return access_token, refresh_token

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        return self._hash_password(password) == password_hash
