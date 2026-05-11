from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.auth import CurrentUser, get_current_user
from app.db import get_db


def db_session() -> Generator[Session, None, None]:
    yield from get_db()


def current_user(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return user
