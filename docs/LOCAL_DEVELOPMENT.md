# Local development (Windows / PowerShell)

## API
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

API: http://127.0.0.1:8000/api/health

## Frontend
Open another terminal from the repository root:
```powershell
cd frontend
npm install
npm run dev
```

UI: http://127.0.0.1:5173

## Camera preview and face detection
```powershell
py -m pip install -r camera_service/requirements.txt
py camera_service/preview.py --source 0
py camera_service/detection.py --source 0
```

Press Q or Escape to stop. Both utilities are local and do not save frames.

## Tests
```powershell
$env:PYTHONPATH="backend;."
py -m pytest -q backend/tests gate_adapter/tests
```

The API is an unauthenticated local prototype. Do not expose it to other machines.
