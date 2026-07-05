from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Optional

from app.core.database import get_connection


@dataclass
class User:
    id: str
    email: str
    full_name: str
    password_hash: str
    refresh_token: Optional[str] = None


class PostgresAuthRepository:
    def __init__(self, dsn: str | None = None) -> None:
        self._dsn = dsn or os.getenv("DATABASE_URL")
        if not self._dsn:
            raise RuntimeError("DATABASE_URL must be configured")

    def _get_connection(self):
        connection = get_connection()
        connection.autocommit = True
        return connection

    def _initialize_schema(self) -> None:
        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS auth_users (
                        id TEXT PRIMARY KEY,
                        email TEXT NOT NULL UNIQUE,
                        full_name TEXT NOT NULL,
                        password_hash TEXT NOT NULL,
                        refresh_token TEXT
                    )
                    """
                )

    async def initialize(self) -> None:
        await asyncio.to_thread(self._initialize_schema)

    async def create_user(
        self,
        *,
        user_id: str,
        email: str,
        full_name: str,
        password_hash: str,
    ) -> User:
        return await asyncio.to_thread(
            self._create_user,
            user_id,
            email,
            full_name,
            password_hash,
        )

    def _create_user(
        self,
        user_id: str,
        email: str,
        full_name: str,
        password_hash: str,
    ) -> User:
        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO auth_users (id, email, full_name, password_hash, refresh_token)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (user_id, email.lower(), full_name, password_hash, None),
                )
        return User(
            id=user_id,
            email=email.lower(),
            full_name=full_name,
            password_hash=password_hash,
        )

    async def get_user_by_email(self, email: str) -> User | None:
        return await asyncio.to_thread(self._get_user_by_email, email)

    def _get_user_by_email(self, email: str) -> User | None:
        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, email, full_name, password_hash, refresh_token FROM auth_users WHERE email = %s",
                    (email.lower(),),
                )
                row = cursor.fetchone()
        if not row:
            return None
        return User(
            id=row[0],
            email=row[1],
            full_name=row[2],
            password_hash=row[3],
            refresh_token=row[4],
        )

    async def get_user_by_id(self, user_id: str) -> User | None:
        return await asyncio.to_thread(self._get_user_by_id, user_id)

    def _get_user_by_id(self, user_id: str) -> User | None:
        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, email, full_name, password_hash, refresh_token FROM auth_users WHERE id = %s",
                    (user_id,),
                )
                row = cursor.fetchone()
        if not row:
            return None
        return User(
            id=row[0],
            email=row[1],
            full_name=row[2],
            password_hash=row[3],
            refresh_token=row[4],
        )

    async def update_refresh_token(self, user_id: str, refresh_token: str | None) -> None:
        await asyncio.to_thread(self._update_refresh_token, user_id, refresh_token)

    def _update_refresh_token(self, user_id: str, refresh_token: str | None) -> None:
        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE auth_users SET refresh_token = %s WHERE id = %s",
                    (refresh_token, user_id),
                )

    async def get_user_by_refresh_token(self, refresh_token: str) -> User | None:
        return await asyncio.to_thread(self._get_user_by_refresh_token, refresh_token)

    def _get_user_by_refresh_token(self, refresh_token: str) -> User | None:
        with self._get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, email, full_name, password_hash, refresh_token FROM auth_users WHERE refresh_token = %s",
                    (refresh_token,),
                )
                row = cursor.fetchone()
        if not row:
            return None
        return User(
            id=row[0],
            email=row[1],
            full_name=row[2],
            password_hash=row[3],
            refresh_token=row[4],
        )
