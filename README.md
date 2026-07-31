# AI Personal Tutor

Minimal monorepo containing a Next.js frontend and a FastAPI backend.

## Backend
- Location: `backend/app`
- Python dependencies: `fastapi`, `uvicorn[standard]`

Install and run:

```bash
python -m pip install -r backend/requirements.txt
uvicorn app.main:app --reload --port 8000 --app-dir backend/app
```

Health endpoints:
- `GET /` — welcome message
- `GET /health` — status OK

## Frontend
- Location: `frontend/` (Next.js)

Install and run:

```bash
cd frontend
npm install
npm run dev
```

## Notes
- Tested files inspected: `backend/app/main.py`, `frontend/package.json`
**TO BE CONTINUED**
