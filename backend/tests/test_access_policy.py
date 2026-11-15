from datetime import datetime, timedelta, timezone
from app.access_policy import evaluate_access

def check(**changes):
    args=dict(identity_verified=True,person_active=True,gate_enabled=True,has_permission=True)
    args.update(changes)
    return evaluate_access(**args)

def test_permitted():
    assert check().allowed

def test_unknown_is_denied():
    assert check(identity_verified=False).reason == "identity_verification_required"

def test_inactive_is_denied():
    assert not check(person_active=False).allowed

def test_gate_disabled():
    assert not check(gate_enabled=False).allowed

def test_permission_missing():
    assert not check(has_permission=False).allowed

def test_expired_permission():
    assert check(permission_expires_at=datetime.now(timezone.utc)-timedelta(seconds=1)).reason=="permission_expired"
