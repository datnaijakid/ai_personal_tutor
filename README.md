# AI Personal Tutor

AI Personal Tutor is a simple monorepo that combines a FastAPI backend with a Next.js frontend for an early tutoring-style web app.

## Project overview
- Backend API lives in `backend/app`
- Frontend app lives in `frontend/`
- Uploaded files are stored locally in `backend/uploads`

## Backend
- Main entrypoint: `backend/app/main.py`
- Health routes: `backend/app/api/health.py`
- Upload route: `backend/app/api/upload.py`
- Python dependencies are listed in `backend/requirements.txt`

Install and run:

```bash
python -m pip install -r backend/requirements.txt
uvicorn app.main:app --reload --port 8000 --app-dir backend/app
```

Available backend routes:
- `GET /` — welcome message
- `GET /health` — returns a status response
- `POST /upload` — accepts a file upload and saves it locally

## Frontend
- Location: `frontend/`
- Built with Next.js and React

Install and run:

```bash
cd frontend
npm install
npm run dev
```

## Notes
- This project is still in early development.
- File uploads are currently stored locally under `backend/uploads`.
- The current implementation was tested against the backend entrypoint and frontend package configuration.
