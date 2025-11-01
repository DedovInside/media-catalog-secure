import asyncio
import os
import sys
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

os.environ["ENV"] = "test"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)
    yield loop

    try:
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    finally:
        loop.close()


@pytest.fixture(autouse=True, scope="function")
def cleanup_before_each_test():
    """Очистка БД ПЕРЕД каждым тестом - СИНХРОННО"""

    def sync_cleanup():
        """Синхронная очистка через psycopg2 (НЕ asyncpg)"""
        import psycopg2

        from app.core.database import get_db_secrets

        try:
            secrets = get_db_secrets()
            conn = psycopg2.connect(
                host=secrets["DB_HOST"],
                port=secrets["DB_PORT"],
                database=secrets["DB_NAME"],
                user=secrets["DB_USER"],
                password=secrets["DB_PASSWORD"],
            )

            with conn.cursor() as cur:
                # Проверяем существование таблицы
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'media'
                    )
                """
                )

                if cur.fetchone()[0]:
                    cur.execute("TRUNCATE TABLE media RESTART IDENTITY CASCADE")
                    conn.commit()
                    print("Database cleaned before test")

            conn.close()

        except Exception as e:
            print(f"Cleanup failed: {e}")

    # Выполняем cleanup ПЕРЕД каждым тестом
    sync_cleanup()
    yield


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """Simple TestClient БЕЗ cleanup в fixture"""
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
