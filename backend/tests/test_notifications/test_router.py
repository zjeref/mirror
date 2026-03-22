import pytest


@pytest.mark.asyncio
async def test_get_default_preferences(auth_client, test_user):
    """GET /api/notifications/preferences returns default prefs for new user."""
    resp = await auth_client.get("/api/notifications/preferences")
    assert resp.status_code == 200

    data = resp.json()
    assert data["preferred_session_time"] == "evening"
    assert data["notification_enabled"] is False
    assert data["max_notifications_per_day"] == 2
    assert data["quiet_hours_start"] == "22:00"
    assert data["quiet_hours_end"] == "08:00"


@pytest.mark.asyncio
async def test_update_preferences_and_verify(auth_client, test_user):
    """PUT /api/notifications/preferences updates prefs, then GET verifies."""
    update_body = {
        "preferred_session_time": "morning",
        "notification_enabled": True,
        "max_notifications_per_day": 5,
        "quiet_hours_start": "23:00",
        "quiet_hours_end": "07:00",
    }
    resp = await auth_client.put("/api/notifications/preferences", json=update_body)
    assert resp.status_code == 200

    data = resp.json()
    assert data["preferred_session_time"] == "morning"
    assert data["notification_enabled"] is True
    assert data["max_notifications_per_day"] == 5

    # Verify with GET
    resp2 = await auth_client.get("/api/notifications/preferences")
    assert resp2.status_code == 200

    data2 = resp2.json()
    assert data2["preferred_session_time"] == "morning"
    assert data2["notification_enabled"] is True
    assert data2["max_notifications_per_day"] == 5
    assert data2["quiet_hours_start"] == "23:00"
    assert data2["quiet_hours_end"] == "07:00"


@pytest.mark.asyncio
async def test_update_preferences_partial(auth_client, test_user):
    """PUT /api/notifications/preferences with partial data only updates provided fields."""
    resp = await auth_client.put(
        "/api/notifications/preferences",
        json={"notification_enabled": True},
    )
    assert resp.status_code == 200

    data = resp.json()
    assert data["notification_enabled"] is True
    # Other fields remain default
    assert data["preferred_session_time"] == "evening"
    assert data["max_notifications_per_day"] == 2
