#Юнит-тесты (tests/unit/)

import pytest
from unittest.mock import AsyncMock
from src.interact_postgres import interact_postgreSQL_database

@pytest.fixture
def db():
    return interact_postgreSQL_database("postgresql://test")

@pytest.mark.asyncio
async def test_store_link(db, mocker):
    mock_conn = AsyncMock()
    db.pool = AsyncMock()
    db.pool.acquire.return_value.__aenter__.return_value = mock_conn
    
    await db.store_link("long", "short", 1, False, None)
    mock_conn.execute.assert_called_once()

@pytest.mark.asyncio
async def test_purge_old_links(db, mocker):
    mock_conn = AsyncMock()
    db.pool = AsyncMock()
    db.pool.acquire.return_value.__aenter__.return_value = mock_conn
    
    await db.purge_old_links()
    assert mock_conn.execute.call_count == 2