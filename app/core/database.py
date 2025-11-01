import logging
import os
from typing import AsyncGenerator, Dict

import hvac
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# КЭШ СЕКРЕТОВ (один раз на процесс)
_secrets_cache: Dict[str, dict] = {}


def get_db_secrets() -> dict:
    """Get database secrets with caching. Fails fast if secrets are unavailable."""
    env = os.getenv("ENV", "local").lower()

    if env in _secrets_cache:
        return _secrets_cache[env]

    if env in ("local", "test"):
        try:
            client = hvac.Client(url=os.getenv("VAULT_ADDR", "http://127.0.0.1:8200"))
            client.token = os.getenv("VAULT_TOKEN")
            if not client.is_authenticated():
                raise RuntimeError("Vault authentication failed: invalid or missing VAULT_TOKEN")
            
            path = "media-catalog/database" if env == "local" else "media-catalog/test"
            secret = client.secrets.kv.v2.read_secret_version(
                path=path,
                raise_on_deleted_version=True
            )
            secrets = secret["data"]["data"]
        except Exception as e:
            # НЕ используем fallback
            raise RuntimeError(
                f"Failed to load secrets from Vault for ENV={env}. "
                f"Ensure Vault is running and VAULT_TOKEN is set. Original error: {e}"
            ) from e

    elif env == "ci":
        required = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]
        secrets = {}
        for var in required:
            value = os.getenv(var)
            if not value:
                raise RuntimeError(f"Missing required CI secret: {var}")
            secrets[var] = value

    else:
        raise ValueError(f"Unknown ENV: {env}")

    _secrets_cache[env] = secrets
    return secrets


# ОДИН URL с параметром драйвера
def create_database_url(driver: str) -> str:
    secrets = get_db_secrets()
    return (
        f"postgresql+{driver}://{secrets['DB_USER']}:{secrets['DB_PASSWORD']}"
        f"@{secrets['DB_HOST']}:{secrets['DB_PORT']}/{secrets['DB_NAME']}"
    )


# ENGINES
async_engine = create_async_engine(
    create_database_url("asyncpg"),
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=20,
    max_overflow=0,
)

sync_engine = create_engine(
    create_database_url("psycopg2"),
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
    future=True,
)

# SESSION
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency для database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    from app.models.base import Base

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    from app.models.base import Base

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ДЛЯ ALEMBIC
DATABASE_URL = create_database_url("psycopg2")
