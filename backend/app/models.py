from . import db, utcnow

class Person(db.Model):
    __tablename__ = "people"
    id = db.Column(db.Integer, primary_key=True)
    university_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    full_name = db.Column(db.String(180), nullable=False)
    department = db.Column(db.String(180), nullable=False)
    role = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    def to_dict(self):
        return {key: getattr(self, key) for key in ("id", "university_id", "full_name", "department", "role", "status")}

class Gate(db.Model):
    __tablename__ = "gates"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(200), nullable=False, default="")
    enabled = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        return {key: getattr(self, key) for key in ("id", "name", "location", "enabled")}

class AccessEvent(db.Model):
    __tablename__ = "access_events"
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey("people.id"), nullable=False)
    gate_id = db.Column(db.Integer, db.ForeignKey("gates.id"), nullable=False)
    direction = db.Column(db.String(10), nullable=False)
    decision = db.Column(db.String(30), nullable=False)
    source = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id, "person_id": self.person_id, "gate_id": self.gate_id,
            "direction": self.direction, "decision": self.decision, "source": self.source,
            "created_at": self.created_at.isoformat(),
        }


class AccessPermission(db.Model):
    """Explicit gate assignment. Does not authorize physical gate activation."""
    __tablename__ = "access_permissions"
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey("people.id"), nullable=False, index=True)
    gate_id = db.Column(db.Integer, db.ForeignKey("gates.id"), nullable=False, index=True)
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (db.UniqueConstraint("person_id", "gate_id", name="uq_person_gate"),)

    def to_dict(self):
        return {"id": self.id, "person_id": self.person_id, "gate_id": self.gate_id, "enabled": self.enabled}
