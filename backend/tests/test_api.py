import pytest
from app import create_app

@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}"})
    return app.test_client()

def test_health(client):
    assert client.get("/api/health").json["status"] == "ok"

def test_person_and_event(client):
    person = client.post("/api/people", json={
        "university_id": "U-001", "full_name": "Demo Student",
        "department": "Computer Engineering", "role": "student"
    })
    assert person.status_code == 201
    gate = client.post("/api/gates", json={"name": "Main Entrance"})
    assert gate.status_code == 201
    event = client.post("/api/events", json={"person_id": person.json["id"], "gate_id": gate.json["id"], "direction": "entry"})
    assert event.status_code == 201
    assert event.json["decision"] == "manual_review"

def test_validation(client):
    assert client.post("/api/people", json={}).status_code == 400
    assert client.post("/api/events", json={"direction": "entry"}).status_code == 400
