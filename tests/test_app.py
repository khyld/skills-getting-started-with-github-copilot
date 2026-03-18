import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the activities dict to its original state after each test."""
    original = {
        name: {**data, "participants": list(data["participants"])}
        for name, data in activities.items()
    }
    yield
    activities.clear()
    activities.update(original)


# --- GET /activities ---

def test_get_activities_returns_all():
    # Arrange - no setup needed, activities are pre-loaded

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data


def test_get_activities_structure():
    # Arrange - no setup needed, activities are pre-loaded

    # Act
    response = client.get("/activities")

    # Assert
    activity = response.json()["Chess Club"]
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity


# --- GET / redirect ---

def test_root_redirects_to_index():
    # Arrange - no setup needed

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"] == "/static/index.html"


# --- POST /activities/{activity_name}/signup ---

def test_signup_success():
    # Arrange
    email = "newstudent@mergington.edu"
    activity_name = "Chess Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email in response.json()["message"]
    assert email in activities[activity_name]["participants"]


def test_signup_activity_not_found():
    # Arrange
    email = "student@mergington.edu"
    activity_name = "Nonexistent Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_student():
    # Arrange - michael is already in Chess Club
    email = "michael@mergington.edu"
    activity_name = "Chess Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_activity_full():
    # Arrange - fill Chess Club (max 12, starts with 2) to capacity
    activity_name = "Chess Club"
    for i in range(10):
        activities[activity_name]["participants"].append(f"extra{i}@mergington.edu")

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "overflow@mergington.edu"},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


# --- DELETE /activities/{activity_name}/signup ---

def test_unregister_success():
    # Arrange
    email = "michael@mergington.edu"
    activity_name = "Chess Club"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email in response.json()["message"]
    assert email not in activities[activity_name]["participants"]


def test_unregister_activity_not_found():
    # Arrange
    email = "michael@mergington.edu"
    activity_name = "Nonexistent Club"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_student_not_registered():
    # Arrange
    email = "notregistered@mergington.edu"
    activity_name = "Chess Club"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not registered for this activity"
