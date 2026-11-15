import os
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def utcnow():
    return datetime.now(timezone.utc)

def create_app(test_config=None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///smart_gate.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")}})
    from .models import Person, Gate, AccessEvent
    with app.app_context():
        db.create_all()

    @app.get("/api/health")
    def health():
        return jsonify(status="ok", service="university-smart-gate")

    @app.get("/api/dashboard")
    def dashboard():
        return jsonify(
            people=db.session.query(Person).count(),
            gates=db.session.query(Gate).count(),
            events=db.session.query(AccessEvent).count(),
            recent=[event.to_dict() for event in AccessEvent.query.order_by(AccessEvent.id.desc()).limit(8).all()],
        )

    @app.get("/api/people")
    def list_people():
        return jsonify([p.to_dict() for p in Person.query.order_by(Person.id.desc()).all()])

    @app.post("/api/people")
    def create_person():
        data = request.get_json(silent=True) or {}
        required = ("university_id", "full_name", "department", "role")
        if any(not isinstance(data.get(key), str) or not data[key].strip() for key in required):
            return jsonify(error="university_id, full_name, department and role are required"), 400
        if data["role"] not in ("student", "staff", "faculty", "visitor"):
            return jsonify(error="invalid role"), 400
        if Person.query.filter_by(university_id=data["university_id"].strip()).first():
            return jsonify(error="university_id already exists"), 409
        person = Person(
            university_id=data["university_id"].strip()[:64],
            full_name=data["full_name"].strip()[:180],
            department=data["department"].strip()[:180],
            role=data["role"],
        )
        db.session.add(person)
        db.session.commit()
        return jsonify(person.to_dict()), 201

    @app.get("/api/gates")
    def list_gates():
        return jsonify([g.to_dict() for g in Gate.query.order_by(Gate.id).all()])

    @app.post("/api/gates")
    def create_gate():
        data = request.get_json(silent=True) or {}
        name = data.get("name")
        if not isinstance(name, str) or not name.strip():
            return jsonify(error="name required"), 400
        gate = Gate(name=name.strip()[:120], location=str(data.get("location") or "")[:200])
        db.session.add(gate)
        db.session.commit()
        return jsonify(gate.to_dict()), 201

    @app.get("/api/events")
    def list_events():
        return jsonify([e.to_dict() for e in AccessEvent.query.order_by(AccessEvent.id.desc()).limit(100).all()])

    @app.post("/api/events")
    def record_event():
        # Prototype only: operator-entered access records, never automatic facial identity assertions.
        data = request.get_json(silent=True) or {}
        person = db.session.get(Person, data.get("person_id")) if isinstance(data.get("person_id"), int) else None
        gate = db.session.get(Gate, data.get("gate_id")) if isinstance(data.get("gate_id"), int) else None
        if not person or not gate or data.get("direction") not in ("entry", "exit"):
            return jsonify(error="valid person_id, gate_id and direction required"), 400
        event = AccessEvent(person_id=person.id, gate_id=gate.id, direction=data["direction"], decision="manual_review", source="operator")
        db.session.add(event)
        db.session.commit()
        return jsonify(event.to_dict()), 201

    return app
