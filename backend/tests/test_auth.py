import pytest
from app import create_app

def test_guard_requires_secret(monkeypatch,tmp_path):
    monkeypatch.delenv("SMART_GATE_API_TOKEN",raising=False)
    with pytest.raises(RuntimeError,match="SMART_GATE_API_TOKEN"):
        create_app({"SQLALCHEMY_DATABASE_URI":f"sqlite:///{tmp_path/'guard.db'}"})

def test_authentication(monkeypatch,tmp_path):
    token="A"*40
    monkeypatch.setenv("SMART_GATE_API_TOKEN",token)
    app=create_app({"SQLALCHEMY_DATABASE_URI":f"sqlite:///{tmp_path/'auth.db'}"})
    client=app.test_client()
    assert client.get("/api/health").status_code==200
    assert client.get("/api/people").status_code==401
    assert client.get("/api/events/export.csv").status_code==401
    assert client.get("/api/people",headers={"Authorization":"Bearer wrong"}).status_code==401
    res=client.get("/api/people",headers={"Authorization":"Bearer "+token})
    assert res.status_code==200
    assert res.headers["Cache-Control"]=="no-store"
