import csv
import io
import pytest
from app import create_app

@pytest.fixture
def client(tmp_path):
    app=create_app({"TESTING":True,"SQLALCHEMY_DATABASE_URI":f"sqlite:///{tmp_path / 'audit.db'}"})
    return app.test_client()

def test_filter_and_csv_export(client):
    person=client.post("/api/people",json={"university_id":"AUD-1","full_name":"Auditor","department":"Engineering","role":"staff"}).json
    gate=client.post("/api/gates",json={"name":"Test Gate"}).json
    pid,gid=person["id"],gate["id"]
    for direction in ("entry","exit"):
        assert client.post("/api/events",json={"person_id":pid,"gate_id":gid,"direction":direction}).status_code==201
    events=client.get(f"/api/events?person_id={pid}&gate_id={gid}&direction=entry")
    assert events.status_code==200
    assert len(events.json)==1
    assert events.json[0]["direction"]=="entry"
    response=client.get(f"/api/events/export.csv?direction=exit")
    assert response.status_code==200
    rows=list(csv.DictReader(io.StringIO(response.get_data(as_text=True))))
    assert len(rows)==1
    assert rows[0]["direction"]=="exit"
    assert response.headers["Cache-Control"]=="no-store"

def test_audit_filters_fail_validation(client):
    assert client.get("/api/events?person_id=-1").status_code==400
    assert client.get("/api/events?direction=other").status_code==400
    assert client.get("/api/events?limit=10000").status_code==400
    assert client.get("/api/events/export.csv?gate_id=oops").status_code==400
