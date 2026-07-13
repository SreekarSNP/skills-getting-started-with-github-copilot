import copy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client():
    return TestClient(app_module.app)


@pytest.fixture(autouse=True)
def reset_activities_state():
    original_state = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(original_state))


def test_get_activities_returns_200_and_expected_structure(client):
    # Arrange
    expected_fields = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")
    payload = response.json()

    # Assert
    assert response.status_code == 200
    assert isinstance(payload, dict)
    assert "Chess Club" in payload
    assert expected_fields.issubset(payload["Chess Club"].keys())


def test_signup_returns_200_and_adds_participant(client):
    # Arrange
    activity_name = "Chess Club"
    new_email = "new.student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": new_email})
    activities_response = client.get("/activities")
    activities_payload = activities_response.json()

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {new_email} for {activity_name}"
    assert new_email in activities_payload[activity_name]["participants"]


def test_signup_returns_404_when_activity_not_found(client):
    # Arrange
    missing_activity = "Not A Real Activity"

    # Act
    response = client.post(f"/activities/{missing_activity}/signup", params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_returns_400_when_student_already_registered(client):
    # Arrange
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": existing_email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_unregister_returns_200_and_removes_participant(client):
    # Arrange
    activity_name = "Programming Class"
    existing_email = "emma@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": existing_email},
    )
    activities_response = client.get("/activities")
    activities_payload = activities_response.json()

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {existing_email} from {activity_name}"
    assert existing_email not in activities_payload[activity_name]["participants"]


def test_unregister_returns_404_when_activity_not_found(client):
    # Arrange
    missing_activity = "Not A Real Activity"

    # Act
    response = client.delete(
        f"/activities/{missing_activity}/participants",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_404_when_student_not_signed_up(client):
    # Arrange
    activity_name = "Art Studio"
    absent_email = "not.signed.up@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": absent_email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not signed up for this activity"


def test_signup_then_unregister_updates_participants_state(client):
    # Arrange
    activity_name = "Debate Team"
    email = "sequence.student@mergington.edu"

    # Act
    signup_response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
    after_signup_payload = client.get("/activities").json()
    unregister_response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )
    after_unregister_payload = client.get("/activities").json()

    # Assert
    assert signup_response.status_code == 200
    assert email in after_signup_payload[activity_name]["participants"]
    assert unregister_response.status_code == 200
    assert email not in after_unregister_payload[activity_name]["participants"]
