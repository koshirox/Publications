import os
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User

password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)


def get_db():
    with SessionLocal() as session:
        yield session


Db = Annotated[Session, Depends(get_db)]


def jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("Укажите JWT_SECRET длиной от 32 символов в .env")
    return secret


def create_token(user: User) -> str:
    expires = datetime.now(UTC) + timedelta(hours=1)
    return jwt.encode({"sub": str(user.id), "exp": expires}, jwt_secret(), algorithm="HS256")


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(401, detail, headers={"WWW-Authenticate": "Bearer"})


def current_user(
    db: Db,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    if credentials is None:
        raise unauthorized("Войдите и передайте JWT")
    try:
        payload = jwt.decode(
            credentials.credentials, jwt_secret(), algorithms=["HS256"],
            options={"require": ["sub", "exp"]},
        )
        user_id = int(payload["sub"])
        if not 0 < user_id < 2**63:
            raise ValueError("Недопустимый ID")
    except (jwt.InvalidTokenError, ValueError):
        raise unauthorized("Неверный или просроченный токен") from None
    user = db.get(User, user_id)
    if user is None:
        raise unauthorized("Пользователь не найден")
    return user


CurrentUser = Annotated[User, Depends(current_user)]
