from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.logging import logger


def _get_engine():
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql"):
        try:
            eng = create_engine(
                db_url,
                pool_pre_ping=True,
                echo=(settings.ENVIRONMENT == "development"),
                connect_args={"connect_timeout": 3},
            )
            with eng.connect() as conn:
                pass
            return eng
        except Exception:
            logger.warning(
                "PostgreSQL connection unavailable. Falling back to local SQLite database (agentcart.db)."
            )
            return create_engine(
                "sqlite:///./agentcart.db",
                connect_args={"check_same_thread": False},
            )
    else:
        connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
        return create_engine(db_url, pool_pre_ping=True, connect_args=connect_args)


engine = _get_engine()


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.x ORM models."""

    pass
