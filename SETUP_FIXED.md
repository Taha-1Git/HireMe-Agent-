# TrueHire AI - Fixed Setup Guide

## What was fixed

- Moved React/Next.js `.tsx` files out of `backend/app/services` into `frontend/components`.
- Added missing `frontend/lib/utils.ts` for `cn()`.
- Added missing `frontend/components/ui/button.tsx`.
- Added missing `frontend/components/PulsePerimeter.tsx` and `ReportDashboard.tsx`.
- Fixed wrong CSS import in `frontend/app/layout.tsx`.
- Added `baseUrl` in `frontend/tsconfig.json` so `@/...` imports work.
- Added missing frontend dependencies: `clsx`, `tailwind-merge`.
- Fixed invalid TensorFlow face landmarks package version to `^1.0.6`.
- Fixed backend run command to use `uvicorn app.main:app`.
- Updated root npm scripts to use npm instead of pnpm.

## Requirements

Install these first:

- Python 3.10 or newer
- Node.js 18 or newer
- npm

## Backend setup

Open terminal in the project root:

```bash
cd backend
python -m venv venv
```

Activate the virtual environment:

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Windows CMD:

```cmd
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

Install backend packages:

```bash
pip install -r requirements.txt
```

Run backend:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Check backend in browser:

```text
http://localhost:8000/api/health
```

You should see:

```json
{"status":"ok","service":"truehire-backend"}
```

## Frontend setup

Open another terminal in the project root:

```bash
cd frontend
npm install
npm run dev
```

Open frontend:

```text
http://localhost:3000
```

## Run both from root

After installing both backend and frontend dependencies once:

```bash
npm install
npm run dev
```

## Deployment suggestion

For a hackathon demo:

- Deploy frontend on Vercel.
- Deploy backend on Render or Railway.
- For backend start command use:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- Add environment variables on backend hosting:

```text
DEBUG=False
DATABASE_URL=sqlite:///./truehire.db
ALLOWED_ORIGINS=["https://your-vercel-app.vercel.app"]
OPENAI_API_KEY=your_real_key
DEMO_MODE=true
```

- Add environment variable on Vercel frontend:

```text
NEXT_PUBLIC_API_URL=https://your-backend-url.onrender.com/api
NEXT_PUBLIC_DEMO_MODE=true
```
