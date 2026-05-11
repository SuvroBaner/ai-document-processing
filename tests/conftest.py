"""Shared pytest fixtures.

The tests in this scaffold run against an in-memory SQLite for speed; the
schema we use is also Postgres-compatible. Production runs against Postgres
(see docker-compose.yml).
"""

from __future__ import annotations

import os
from typing import Generator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base

# Import every models module so Base.metadata is populated.
from app.common import audit as _audit  # noqa: F401
from app.extraction import models as _extraction_models  # noqa: F401
from app.ingestion import models as _ingestion_models  # noqa: F401
from app.output import models as _output_models  # noqa: F401
from app.plans import models as _plans_models  # noqa: F401
from app.projects import models as _projects_models  # noqa: F401
from app.review import models as _review_models  # noqa: F401
from app.vocabulary import models as _vocabulary_models  # noqa: F401
from app.workflow import models as _workflow_models  # noqa: F401

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:", future=True)

    # SQLite doesn't have gen_random_uuid(); patch in a Python default.
    from uuid import uuid4
    import sqlalchemy.sql.functions as fn

    @event.listens_for(eng, "do_connect")
    def _fk(_conn, _branch):  # noqa: ARG001
        pass

    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine) -> Generator[Session, None, None]:
    Sess = sessionmaker(bind=engine, future=True)
    s = Sess()
    try:
        yield s
    finally:
        s.close()
