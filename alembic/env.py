from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import get_settings
from app.db import Base

# Import all model modules so Base.metadata is populated.
from app.common import audit  # noqa: F401
from app.extraction import models as _extraction_models  # noqa: F401
from app.ingestion import models as _ingestion_models  # noqa: F401
from app.output import models as _output_models  # noqa: F401
from app.plans import models as _plans_models  # noqa: F401
from app.projects import models as _projects_models  # noqa: F401
from app.review import models as _review_models  # noqa: F401
from app.vocabulary import models as _vocabulary_models  # noqa: F401
from app.workflow import models as _workflow_models  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
