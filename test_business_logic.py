
# Юнит-тесты (tests/unit/)
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from business_logic import business_logic_shortlink

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def logic(mock_db):
    return business_logic_shortlink(mock_db)

@pytest.mark.asyncio
async def test_short_link_building(logic, mock_db):
    mock_db.search_at_the_source_url_short_link.return_value = None
    mock_db.store_link.return_value = None
    
    result = await logic.short_link_building("http://example.com")
    assert result["status_code"] == 201
    assert len(result["short_link"]) == 6

@pytest.mark.asyncio
async def test_generate_short_link_custom_alias(logic, mock_db):
    mock_db.search_at_the_source_url_short_link.return_value = None
    
    result = await logic.generate_short_link_custom_alias(
        "http://example.com", "custom"
    )
    assert result["short_link"] == "custom"

@pytest.mark.asyncio
async def test_get_original_url(logic, mock_db):
    mock_db.search_at_the_source_url_short_link.return_value = "http://example.com"
    mock_db.saves_short_link_access_statistics_table.return_value = None
    
    result = await logic.get_original_url("abc123")
    assert result == "http://example.com"