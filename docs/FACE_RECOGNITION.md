# Local Face Recognition Prototype

**Important:** This is a research/demo prototype. OpenCV Haar detection and LBPH recognition are not validated for physical access control. Face recognition results are *candidate matches*, not proof of identity. No gate actuation is connected. False positives and false negatives are possible.

## Setup (Windows PowerShell)

1. Pull the `develop` branch.
2. Update the backend packages: `cd backend; .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt`.
3. Generate a token in the **same terminal** as the backend:

```powershell
$env:SMART_GATE_API_TOKEN = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
.\\.venv\\Scripts\\python.exe run.py
```

4. In another terminal, run `cd frontend; npm install; npm run dev`.
5. Open http://localhost:5173 and sign in using the printed token.
6. Add people under **People**, open **Enrollment**, choose a person, confirm consent, capture one well-lit face and click **Enroll selected person**.
7. On **Overview**, click **Start monitoring**. The large camera shows face rectangles and candidate names; the right-side panel shows recent recognition events. Unknown faces produce a visual warning.
8. You may delete an enrollment on the Enrollment screen. The original JPEG is never saved; a derived face template is saved to `backend/instance/face_templates` by default. Treat this directory as sensitive personal data, restrict access and delete it when the demonstration ends.

## Constraints and cautions

- Only one enrolled face template per person. Existing person enrollment is rejected.
- Similar-looking face enrollment is rejected for human review, but duplicate detection is **not guaranteed**. Test multiple photos of the same person under different lighting and pose.
- Recognition distance threshold (55) and duplicate review threshold (65) are **provisional**, not calibrated. No accuracy claim should be made until a held-out evaluation.
- One unknown-person warning may represent multiple people. Unknown does not mean dangerous.
- The activity panel updates roughly every 1.5 seconds and deduplicates events for 8 seconds; it is not a reliable passage counter or permanent audit log.
- No spoof detection, no anti-tailgating, no proof of gate crossing, no biometric encryption at rest, no per-user RBAC, and no retention automation.
- The backend token is only a development guard. Never expose the service on a campus network. Use a local demo with consenting adult participants and provide a non-biometric alternative.
- Do not use this system for disciplinary actions or automatic admission/denial.
