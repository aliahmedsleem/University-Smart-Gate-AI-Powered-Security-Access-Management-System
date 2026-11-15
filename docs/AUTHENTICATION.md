# Local operator API token (development)

The backend now refuses to start without a random `SMART_GATE_API_TOKEN` of at least 32 characters (except when running the test suite with `TESTING=True`). All API endpoints other than `/api/health` require `Authorization: Bearer <token>`.

## Windows PowerShell

From the repository root:

```powershell
$env:SMART_GATE_API_TOKEN = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
$env:SMART_GATE_API_TOKEN
cd backend
.\.venv\Scripts\python.exe run.py
```

Copy the token printed in PowerShell into the sign-in screen at http://localhost:5173. Keep the backend terminal running. The token is stored in browser memory only; refreshing the page requires signing in again. Set the same token each time you restart the backend if needed. Do not commit the token or share screenshots containing it.

This is a **single-operator development guard**, not production-ready authentication. No per-user roles, audit attribution, login rate limiting, account lockout or secure multi-user sessions are implemented. Run only on localhost. Before campus deployment: HTTPS, user accounts, MFA, RBAC, CSRF/session hardening or proper OAuth/OIDC, rotation/revocation, and access logging are required.

## Run tests

```powershell
$env:PYTHONPATH = "backend;."
py -m pytest -q backend/tests gate_adapter/tests
cd frontend
npm install
npm run build
```
