"""
Tests for the High School Management System API

Uses AAA (Arrange-Act-Assert) pattern for clear test structure.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Arrange: Provide a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """
    Arrange: Reset activities to initial state before each test.
    
    This fixture ensures each test starts with a clean state to avoid
    test interdependencies.
    """
    from src.app import activities
    
    # Store initial state
    initial_state = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Club": {
            "description": "Practice basketball skills and play team games",
            "schedule": "Mondays, 3:30 PM - 5:00 PM",
            "max_participants": 20,
            "participants": []
        },
        "Track and Field": {
            "description": "Train for running, jumping, and throwing events",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": []
        },
        "Art Club": {
            "description": "Explore drawing, painting, and other visual art techniques",
            "schedule": "Tuesdays, 3:30 PM - 5:00 PM",
            "max_participants": 15,
            "participants": []
        },
        "Drama Club": {
            "description": "Develop acting skills and create theatrical productions",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 20,
            "participants": []
        },
        "Debate Club": {
            "description": "Build critical thinking and public speaking skills through debate",
            "schedule": "Wednesdays, 3:30 PM - 4:30 PM",
            "max_participants": 16,
            "participants": []
        },
        "Science Club": {
            "description": "Explore scientific ideas through experiments and discussion",
            "schedule": "Fridays, 3:30 PM - 4:30 PM",
            "max_participants": 18,
            "participants": []
        }
    }
    
    # Clear and restore
    activities.clear()
    activities.update(initial_state)
    
    yield
    
    # Cleanup after test
    activities.clear()
    activities.update(initial_state)


# ============================================================================
# GET /activities Tests
# ============================================================================

def test_get_activities_returns_all_activities(client):
    """Test that GET /activities returns all activities."""
    # Arrange
    expected_activity_count = 9
    
    # Act
    response = client.get("/activities")
    
    # Assert
    assert response.status_code == 200
    activities_data = response.json()
    assert len(activities_data) == expected_activity_count
    assert "Chess Club" in activities_data
    assert "Programming Class" in activities_data


def test_get_activities_contains_correct_structure(client):
    """Test that activities have correct data structure."""
    # Arrange
    expected_keys = {"description", "schedule", "max_participants", "participants"}
    
    # Act
    response = client.get("/activities")
    activities_data = response.json()
    
    # Assert
    for activity_name, activity_data in activities_data.items():
        assert isinstance(activity_data, dict)
        assert set(activity_data.keys()) == expected_keys
        assert isinstance(activity_data["participants"], list)
        assert isinstance(activity_data["max_participants"], int)


def test_get_activities_contains_participant_data(client):
    """Test that activities contain expected participant information."""
    # Arrange
    expected_chess_participants = ["michael@mergington.edu", "daniel@mergington.edu"]
    
    # Act
    response = client.get("/activities")
    activities_data = response.json()
    
    # Assert
    chess_club = activities_data["Chess Club"]
    assert chess_club["participants"] == expected_chess_participants
    assert len(chess_club["participants"]) == 2


# ============================================================================
# POST /activities/{activity_name}/signup Tests
# ============================================================================

def test_signup_new_student_success(client):
    """Test successfully signing up a new student for an activity."""
    # Arrange
    activity_name = "Basketball Club"
    email = "new_student@mergington.edu"
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"


def test_signup_adds_participant_to_activity(client):
    """Test that signup correctly adds participant to activity's participant list."""
    # Arrange
    activity_name = "Basketball Club"
    email = "new_student@mergington.edu"
    
    # Act
    client.post(f"/activities/{activity_name}/signup", params={"email": email})
    response = client.get("/activities")
    
    # Assert
    activities_data = response.json()
    assert email in activities_data[activity_name]["participants"]
    assert len(activities_data[activity_name]["participants"]) == 1


def test_signup_duplicate_student_fails(client):
    """Test that duplicate signup returns 400 error."""
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # Already signed up
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_signup_nonexistent_activity_fails(client):
    """Test that signup for non-existent activity returns 404 error."""
    # Arrange
    activity_name = "Nonexistent Club"
    email = "student@mergington.edu"
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_signup_full_activity_fails(client):
    """Test that signup for a full activity returns 400 error."""
    # Arrange
    # Create a test client and get the activities
    from src.app import activities
    
    # Fill up Basketball Club (max 20, currently 0)
    test_activity = activities["Basketball Club"]
    test_emails = [f"student{i}@mergington.edu" for i in range(test_activity["max_participants"])]
    for email in test_emails:
        test_activity["participants"].append(email)
    
    activity_name = "Basketball Club"
    email = "extra_student@mergington.edu"
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 400
    assert "Activity is full" in response.json()["detail"]


def test_signup_multiple_students_different_activities(client):
    """Test signing up multiple students for different activities."""
    # Arrange
    student1_activity = "Basketball Club"
    student1_email = "student1@mergington.edu"
    student2_activity = "Art Club"
    student2_email = "student2@mergington.edu"
    
    # Act
    response1 = client.post(
        f"/activities/{student1_activity}/signup",
        params={"email": student1_email}
    )
    response2 = client.post(
        f"/activities/{student2_activity}/signup",
        params={"email": student2_email}
    )
    
    # Assert
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert student1_email in activities_data[student1_activity]["participants"]
    assert student2_email in activities_data[student2_activity]["participants"]


# ============================================================================
# DELETE /activities/{activity_name}/unregister Tests
# ============================================================================

def test_unregister_student_success(client):
    """Test successfully unregistering a student from an activity."""
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # Already signed up
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity_name}"


def test_unregister_removes_participant_from_activity(client):
    """Test that unregister correctly removes participant from activity's list."""
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    initial_count = 2
    
    # Act
    client.delete(f"/activities/{activity_name}/unregister", params={"email": email})
    response = client.get("/activities")
    
    # Assert
    activities_data = response.json()
    assert email not in activities_data[activity_name]["participants"]
    assert len(activities_data[activity_name]["participants"]) == initial_count - 1


def test_unregister_not_registered_student_fails(client):
    """Test that unregistering a non-registered student returns 400 error."""
    # Arrange
    activity_name = "Basketball Club"
    email = "unregistered@mergington.edu"
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 400
    assert "not registered" in response.json()["detail"]


def test_unregister_nonexistent_activity_fails(client):
    """Test that unregister from non-existent activity returns 404 error."""
    # Arrange
    activity_name = "Nonexistent Club"
    email = "student@mergington.edu"
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_unregister_then_signup_again(client):
    """Test that a student can unregister and then sign up again."""
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    
    # Act - Unregister
    unregister_response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    # Act - Sign up again
    signup_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    # Assert
    assert unregister_response.status_code == 200
    assert signup_response.status_code == 200
    
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert email in activities_data[activity_name]["participants"]


# ============================================================================
# Edge Cases and Integration Tests
# ============================================================================

def test_activity_capacity_boundary(client):
    """Test capacity limits at boundary condition."""
    # Arrange
    from src.app import activities
    
    activity_name = "Drama Club"
    max_capacity = activities[activity_name]["max_participants"]
    
    # Fill to capacity - 1
    for i in range(max_capacity - 1):
        email = f"student{i}@mergington.edu"
        activities[activity_name]["participants"].append(email)
    
    # Act - Add one more (should succeed)
    email_success = "penultimate@mergington.edu"
    response_success = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email_success}
    )
    
    # Act - Try to add another (should fail)
    email_fail = "over_capacity@mergington.edu"
    response_fail = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email_fail}
    )
    
    # Assert
    assert response_success.status_code == 200
    assert response_fail.status_code == 400


def test_concurrent_operations_on_different_activities(client):
    """Test that operations on different activities don't interfere."""
    # Arrange
    email1 = "student1@mergington.edu"
    email2 = "student2@mergington.edu"
    
    # Act
    signup1 = client.post("/activities/Basketball Club/signup", params={"email": email1})
    signup2 = client.post("/activities/Drama Club/signup", params={"email": email2})
    
    # Assert
    assert signup1.status_code == 200
    assert signup2.status_code == 200
    
    response = client.get("/activities")
    activities_data = response.json()
    assert email1 in activities_data["Basketball Club"]["participants"]
    assert email2 in activities_data["Drama Club"]["participants"]
    assert email1 not in activities_data["Drama Club"]["participants"]
    assert email2 not in activities_data["Basketball Club"]["participants"]


def test_root_redirects_to_static_index(client):
    """Test that root path redirects to static index.html."""
    # Arrange - follow_redirects=False to check redirect
    
    # Act
    response = client.get("/", follow_redirects=False)
    
    # Assert
    assert response.status_code == 307
    assert "/static/index.html" in response.headers["location"]
