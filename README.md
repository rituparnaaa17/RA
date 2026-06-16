# SRM Result Analysis

A monorepo containing the **frontend** (Next.js) and **backend** (FastAPI + MySQL) for the SRM Result Analysis tool.

## Project Structure

```
RA/
├── frontend/          # Next.js 16 app (deployed on Vercel)
│   ├── app/           # Next.js App Router pages
│   ├── components/    # UI components
│   ├── lib/           # API client & auth helpers
│   ├── hooks/         # React hooks
│   ├── styles/        # Global styles
│   └── public/        # Static assets
│
└── backend/           # FastAPI Python backend (deployed on Railway)
    ├── main.py        # FastAPI app & all endpoints
    ├── db.py          # SQLAlchemy DB connection
    ├── models.py      # SQLAlchemy ORM models
    ├── config.py      # App configuration
    ├── seed_faculty.py# One-time DB seeder
    ├── requirements.txt
    ├── railway.toml   # Railway deployment config
    ├── services/      # Business logic
    │   ├── parse_excel.py
    │   ├── compute.py
    │   └── render.py
    └── templates/     # Jinja2 HTML report templates
```

## Deployment

| Service  | Platform | URL |
|----------|----------|-----|
| Frontend | Vercel   | https://ra-liart.vercel.app |
| Backend  | Railway  | https://ra-production-8451.up.railway.app |

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Set `NEXT_PUBLIC_API_URL=http://localhost:8000/api` in `frontend/.env.local`.
