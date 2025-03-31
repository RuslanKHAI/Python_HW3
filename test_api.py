# Функциональные тесты (tests/functional/)

import pytest
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_create_short_link(client):
    response = client.post(
        "/links/shorten",
        json={"link": "http://example.com"},
    )
    assert response.status_code == 201
    assert "short_link" in response.json()

@pytest.mark.asyncio
async def test_create_custom_link(client):
    response = client.post(
        "/links/custom_shorten",
        json={"link": "http://example.com", "custom_alias": "custom"},
    )
    assert response.status_code == 201
    assert response.json()["short_link"] == "custom"

@pytest.mark.asyncio
async def test_get_link_stats(client, test_db):
    # Сначала создаем ссылку
    create_resp = client.post(
        "/links/shorten",
        json={"link": "http://example.com"},
    )
    short_code = create_resp.json()["short_link"]
    
    # Тестируем статистику
    stats_resp = client.get(f"/links/{short_code}/stats")
    assert stats_resp.status_code == 401  # Неавторизованный доступ