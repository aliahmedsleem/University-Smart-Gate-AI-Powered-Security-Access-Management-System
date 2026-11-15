import os
from datetime import datetime, timezone
from flask import Flask, jsonify, request, Response
import csv
import io
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
    from .models import Person, Gate, AccessEvent, AccessPermission
    from .access_policy import evaluate_access
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

    def filtered_events():
        query = AccessEvent.query
        for field in ("person_id", "gate_id"):
            raw = request.args.get(field)
            if raw is not None:
                if not raw.isdecimal() or int(raw) <= 0:
                    return None
                query = query.filter(getattr(AccessEvent, field) == int(raw))
        direction = request.args.get("direction")
        if direction is not None:
            if direction not in ("entry", "exit"):
                return None
            query = query.filter(AccessEvent.direction == direction)
        return query

    @app.get("/api/events")
    def list_events():
        query = filtered_events()
        if query is None:
            return jsonify(error="invalid event filter"), 400
        raw_limit = request.args.get("limit", "100")
        if not raw_limit.isdecimal() or not 1 <= int(raw_limit) <= 500:
            return jsonify(error="limit must be between 1 and 500"), 400
        return jsonify([e.to_dict() for e in query.order_by(AccessEvent.id.desc()).limit(int(raw_limit)).all()])

    @app.get("/api/events/export.csv")
    def export_events():
        """Prototype operator CSV export, capped to avoid unbounded memory use."""
        query = filtered_events()
        if query is None:
            return jsonify(error="invalid event filter"), 400
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(("id", "created_at", "person_id", "gate_id", "direction", "decision", "source"))
        for event in query.order_by(AccessEvent.id.desc()).limit(5000).all():
            # Keep exported fields formula-safe for spreadsheet viewers.
            values = (event.id, event.created_at.isoformat(), event.person_id,
                      event.gate_id, event.direction, event.decision, event.source)
            writer.writerow([("'" + v) if isinstance(v, str) and v.startswith(("=", "+", "-", "@")) else v for v in values])
        return Response(output.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition": 'attachment; filename="access-events.csv"',
                                 "Cache-Control": "no-store"})

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


    @app.get("/api/permissions")
    def list_permissions():
        return jsonify([p.to_dict() for p in AccessPermission.query.order_by(AccessPermission.id.desc()).all()])

    @app.post("/api/permissions")
    def assign_permission():
        data = request.get_json(silent=True) or {}
        pid, gid = data.get("person_id"), data.get("gate_id")
        if type(pid) is not int or type(gid) is not int:
            return jsonify(error="person_id and gate_id must be integers"), 400
        if not db.session.get(Person, pid) or not db.session.get(Gate, gid):
            return jsonify(error="person or gate not found"), 404
        existing = AccessPermission.query.filter_by(person_id=pid, gate_id=gid).first()
        if existing:
            return jsonify(error="permission already exists"), 409
        permission = AccessPermission(person_id=pid, gate_id=gid, enabled=True)
        db.session.add(permission)
        db.session.commit()
        return jsonify(permission.to_dict()), 201

    @app.delete("/api/permissions/<int:permission_id>")
    def revoke_permission(permission_id):
        permission = db.session.get(AccessPermission, permission_id)
        if not permission:
            return jsonify(error="permission not found"), 404
        db.session.delete(permission)
        db.session.commit()
        return "", 204

    @app.post("/api/access/check")
    def check_access():
        """Operator-assisted policy preview, not biometric verification or gate control."""
        data = request.get_json(silent=True) or {}
        pid, gid = data.get("person_id"), data.get("gate_id")
        if type(pid) is not int or type(gid) is not int:
            return jsonify(error="person_id and gate_id must be integers"), 400
        person, gate = db.session.get(Person, pid), db.session.get(Gate, gid)
        if not person or not gate:
            return jsonify(error="person or gate not found"), 404
        permission = AccessPermission.query.filter_by(person_id=pid, gate_id=gid, enabled=True).first()
        # Never accept identity_verified from the client as proof of identity.
        # This endpoint returns eligibility only; human identity verification remains required.
        decision = evaluate_access(
            identity_verified=False, person_active=person.status == "active",
            gate_enabled=gate.enabled, has_permission=permission is not None
        )
        return jsonify(allowed=decision.allowed, reason=decision.reason,
                       eligible=bool(person.status == "active" and gate.enabled and permission),
                       identity_verification_required=True,
                       gate_action="none")

    return app
