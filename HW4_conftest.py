# Функциональные тесты (tests/functional/)

import pytest
from fastapi.testclient import TestClient
from app import fastapi_application
from interact_postgres import interact_postgreSQL_database
import asyncpg

@pytest.fixture
def client():
    return TestClient(fastapi_application)

@pytest.fixture(scope="module")
async def test_db():
    db = interact_postgreSQL_database("postgresql://test:test@localhost:5432/test_db")
    await db.connection_database()
    await db.create_database()
    yield db
    await db.pool_database_connection_close()
