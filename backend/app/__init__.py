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
    from .auth import install_api_guard
    install_api_guard(app)
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")}})
    from .models import Person, Gate, AccessEvent, AccessPermission
    from .access_policy import evaluate_access
    from .face_engine import FaceStore, decode_image, extract_faces
    from collections import deque
    import time
    from threading import Lock
    vision_store = FaceStore(os.getenv('SMART_GATE_FACE_DIR', os.path.join(app.instance_path, 'face_templates')))
    from .embedding_engine import EmbeddingEngine, DETECTOR, RECOGNIZER
    embedding_store = EmbeddingEngine(os.getenv('SMART_GATE_FACE_DIR', os.path.join(app.instance_path, 'face_templates'))) if DETECTOR.is_file() and RECOGNIZER.is_file() else None
    vision_log = deque(maxlen=50)
    vision_seq = 0
    vision_lock = Lock()
    last_seen = {}
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


    @app.get("/api/vision/enrollments")
    def vision_enrollments():
        return jsonify(person_ids=embedding_store.enrolled_ids() if embedding_store else vision_store.enrolled_ids(),sample_counts=embedding_store.sample_counts() if embedding_store else vision_store.sample_counts(),engine="sface" if embedding_store else "legacy_lbph",ready=embedding_store is not None)

    @app.post("/api/vision/enroll")
    def vision_enroll():
        data = request.get_json(silent=True) or {}
        pid = data.get("person_id")
        if type(pid) is not int or not data.get("consent_confirmed") is True:
            return jsonify(error="Valid person_id and explicit consent required"), 400
        person = db.session.get(Person, pid)
        if person is None:
            return jsonify(error="person not found"), 404
        try:
            if embedding_store is not None:
                embedding_store.enroll(pid, decode_image(data.get("image")))
                return jsonify(person_id=pid,enrolled=True,engine="sface"),201
            images = data.get("images") if isinstance(data.get("images"), list) else [data.get("image")]
            if not 1 <= len(images) <= 5:
                return jsonify(error="Provide 1 to 5 face captures"), 422
            samples = []
            for image in images:
                faces = extract_faces(decode_image(image))
                if len(faces) != 1:
                    return jsonify(error="Each enrollment capture requires exactly one visible face"), 422
                samples.append(faces[0][1])
            vision_store.enroll_many(pid, samples)
        except ValueError as exc:
            return jsonify(error=str(exc)), 422
        return jsonify(person_id=pid, enrolled=True), 201

    @app.delete("/api/vision/enroll/<int:person_id>")
    def vision_delete(person_id):
        vision_store.delete(person_id)
        if embedding_store is not None:
            embedding_store.delete(person_id)
        return "", 204

    @app.post("/api/vision/recognize")
    def vision_recognize():
        nonlocal vision_seq
        if request.content_length and request.content_length > 3_000_000:
            return jsonify(error="Frame too large"), 413
        data = request.get_json(silent=True) or {}
        try:
            frame = decode_image(data.get("image"))
            faces = [] if embedding_store else extract_faces(frame)
        except ValueError as exc:
            return jsonify(error=str(exc)), 422
        detections = []
        now = time.monotonic()
        matches = embedding_store.recognize(frame) if embedding_store else [{"box":list(box),**vision_store.match(crop)} for box,crop in faces[:12]]
        for match in matches:
            box = match["box"]
            person = db.session.get(Person, match["person_id"]) if match["person_id"] is not None else None
            recognized = bool(person and person.status == "active")
            pid = person.id if recognized else None
            item = {"box":list(box), "recognized":recognized, "person_id":pid,
                    "name":person.full_name if recognized else "Unknown person",
                    "unverified":True}
            detections.append(item)
            key = f"person:{pid}" if recognized else "unknown"
            # Throttle repeated observations; unknown faces cannot be individually identified.
            with vision_lock:
                if now-last_seen.get(key, -1000) >= 8:
                    last_seen[key] = now
                    vision_seq += 1
                    vision_log.appendleft({"id":vision_seq,"name":item["name"],"person_id":pid,
                                           "recognized":recognized,
                                           "timestamp":datetime.now(timezone.utc).isoformat(),
                                           "status":"recognized_candidate" if recognized else "unknown_alert"})
        return jsonify(detections=detections, face_count=len(matches),engine="sface" if embedding_store else "legacy_lbph", gate_action="none",
                       warning="Recognition is advisory only; no gate control or identity verification")

    @app.get("/api/vision/activity")
    def vision_activity():
        with vision_lock:
            return jsonify(list(vision_log))

    return app
