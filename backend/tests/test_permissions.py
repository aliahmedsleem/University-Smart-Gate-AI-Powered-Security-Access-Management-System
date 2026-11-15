import pytest
from app import create_app

@pytest.fixture
def client(tmp_path):
    app=create_app({"TESTING":True,"SQLALCHEMY_DATABASE_URI":f"sqlite:///{tmp_path / 'permissions.db'}"})
    return app.test_client()

def setup(client):
    person=client.post("/api/people",json={"university_id":"P100","full_name":"Test Person","department":"Engineering","role":"student"}).json
    gate=client.post("/api/gates",json={"name":"North Gate"}).json
    return person["id"],gate["id"]

def test_permissions_and_fail_closed_check(client):
    pid,gid=setup(client)
    payload={"person_id":pid,"gate_id":gid}
    before=client.post("/api/access/check",json=payload)
    assert before.status_code==200
    assert before.json["eligible"] is False
    assert before.json["allowed"] is False
    assigned=client.post("/api/permissions",json=payload)
    assert assigned.status_code==201
    assert client.post("/api/permissions",json=payload).status_code==409
    after=client.post("/api/access/check",json={**payload,"identity_verified":True})
    assert after.json["eligible"] is True
    assert after.json["allowed"] is False
    assert after.json["identity_verification_required"] is True
    assert after.json["gate_action"]=="none"
    assert client.delete("/api/permissions/"+str(assigned.json["id"])).status_code==204
    assert client.post("/api/access/check",json=payload).json["eligible"] is False

def test_permissions_reject_invalid_ids(client):
    assert client.post("/api/permissions",json={"person_id":True,"gate_id":1}).status_code==400
    assert client.post("/api/permissions",json={"person_id":1,"gate_id":2}).status_code==404
    assert client.post("/api/access/check",json={}).status_code==400
