# Architecture

- React/Vite frontend: security operations, people, gates and review logs.
- Flask REST API: metadata records and operator-entered access-event logging.
- SQLAlchemy storage: SQLite for local prototype; migrate to PostgreSQL with Alembic before production.
- Camera service: local OpenCV webcam/RTSP preview; does **not** transmit or store frames.
- Future modules: consent-based face enrollment; liveness evaluation; configurable recognizer; isolated gate simulator and hardware adapter.

## Boundaries

This initial foundation does not perform facial recognition, authenticate operators, verify entrants or control physical barriers. Access-event API is explicitly operator-entered and always marked `manual_review`. Do not expose this unauthenticated development backend to a network.

## Security requirements before a pilot

1. SSO/operator authentication and RBAC on every route.
2. Explicit consent, human alternative, deletion workflow and impact assessment for biometric enrollment.
3. Audit logging, encryption, retention schedule, secret management and backup/restore.
4. Dataset consent and independent accuracy/fairness/liveness evaluation.
5. Manual override, emergency egress and fail-safe gate controller, reviewed by campus security.
6. Migrations, input/schema validation and bounded request rates.
