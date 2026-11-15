# Single-photo SFace recognition — troubleshooting Unknown

## Root cause
The previous one-photo feature still used Haar/LBPH. LBPH compares local grayscale texture and its provisional threshold (distance <55) rejects many genuine matches between a reference photograph and webcam images. More enrollment images do not fix that fundamental mismatch.

## Setup (Windows)
From the repository root:

```powershell
git switch develop
git pull --ff-only origin develop
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/download_face_models.py
$env:SMART_GATE_API_TOKEN = [Environment]::GetEnvironmentVariable("SMART_GATE_API_TOKEN","User")
.\.venv\Scripts\python.exe run.py
```

Restart frontend separately with `npm run dev`. On People, the recognition engine must say **sface**. If it says **legacy_lbph**, the model files are missing or the backend has not restarted. Delete old LBPH references, then import one consented, clearly visible JPEG reference per person. Existing LBPH templates cannot be automatically converted into SFace embeddings because original images were intentionally not retained.

## Implementation
OpenCV YuNet detects faces and landmarks, SFace aligns faces and computes a 128-dimensional embedding. Live video compares cosine similarities to reference embeddings. Initial match threshold is 0.45, with a 0.06 separation from the second-best match. These values are **not calibrated**. Do not lower them to force recognition. For a reliable system collect authorized test samples and measure false matches, missed matches, and latency for each camera and pose.

The two ONNX files are downloaded from the OpenCV Zoo project, not committed to Git. Check model licensing before use. No 3D depth, liveness detection, automated identity learning, or gate actuation is implemented. Keep operator review and alternative access available. Treat embeddings as sensitive biometric information.
