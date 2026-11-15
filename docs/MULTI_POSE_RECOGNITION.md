# Multi-pose face recognition prototype

The `develop` branch supports operator-guided 3–5 camera captures per person and a combined frontal/profile Haar detector. The recognizer is still **LBPH**, not ArcFace or 3D depth recognition. These changes may improve tolerance to moderate pose changes but do **not** guarantee side-profile matches, speed or identity accuracy. Profile detection depends on the OpenCV profile cascade being available.

## Updating locally (Windows PowerShell)

```powershell
git switch develop
git pull --ff-only origin develop
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:SMART_GATE_API_TOKEN = [Environment]::GetEnvironmentVariable("SMART_GATE_API_TOKEN", "User")
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe run.py
```

In another PowerShell window, from `frontend`, run `npm install` then `npm run dev`. Paste the previously saved API token in the browser login. Never paste it into issue reports.

## Re-enrollment

Existing one-sample `.npy` enrollments remain readable. To use multi-pose enrollment, open Enrollment, select a person, delete the old enrollment, then capture the same consenting person from front, slightly left, slightly right (optional left/right profile). Every capture must pass basic lighting checks and contain exactly one detected face. Pose labels are **guidance only**; the software does not verify the actual angle. The browser holds captures in memory until submission or reset; the backend saves biometric arrays under `backend/instance/face_templates`.

## Limitations and safety

The system has no liveness or depth sensor, no validated identity threshold, no demographic performance study, and no automatic gate opening. A single RGB webcam cannot reliably infer 3D face depth. For production use, obtain informed consent, validate false-accept and false-reject rates across poses and conditions, encrypt and govern biometric templates, add liveness and human review, and evaluate licensed embedding models such as ArcFace with a suitable detector and alignment pipeline. Do not use this prototype to automatically deny access.
