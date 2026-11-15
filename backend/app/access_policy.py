"""Pure access policy logic, independent of biometric identification.

Unknown/uncertain identities are never treated as authorization.
"""
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    reason: str

def evaluate_access(*, identity_verified: bool, person_active: bool,
                    gate_enabled: bool, has_permission: bool,
                    permission_expires_at: datetime | None = None) -> AccessDecision:
    if not identity_verified:
        return AccessDecision(False, "identity_verification_required")
    if not person_active:
        return AccessDecision(False, "person_inactive")
    if not gate_enabled:
        return AccessDecision(False, "gate_disabled")
    if not has_permission:
        return AccessDecision(False, "permission_missing")
    if permission_expires_at is not None:
        if permission_expires_at.tzinfo is None:
            return AccessDecision(False, "invalid_expiration_timezone")
        if permission_expires_at <= datetime.now(timezone.utc):
            return AccessDecision(False, "permission_expired")
    return AccessDecision(True, "permission_valid")
