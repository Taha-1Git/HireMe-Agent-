# TrueHire AI — Installation & Verification Checklist

## ✅ Project Scaffold Complete

The monorepo foundation for TrueHire AI is now ready. All files have been created and configured.

### Project Statistics

- **Files Created**: 24 core files
- **Directories**: 7 main folders + nested structure
- **Backend Routes**: 1 (health check)
- **Frontend Pages**: 1 (landing with status indicator)
- **Configuration Files**: 8 (pyproject.toml, tsconfig.json, tailwind.config.ts, etc.)
- **Documentation**: 2 (README.md, ARCHITECTURE.md)

---

## 📋 Pre-Installation Requirements

Before running the project, install:

1. **Node.js 18+** (includes npm and npx)
   - Download from: https://nodejs.org/
   - Verify: `node --version`

2. **pnpm** (package manager for frontend)
   - Install: `npm install -g pnpm`
   - Verify: `pnpm --version`

3. **Python 3.11+**
   - Download from: https://www.python.org/
   - Verify: `python --version`

---

## 🚀 Installation Steps

### Step 1: Backend Setup

```bash
cd truehire-ai/backend

# Create Python virtual environment
python -m venv venv

# Activate (choose your OS)
# Windows (PowerShell):
venv\Scripts\Activate.ps1

# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Backend Environment Configuration

```bash
# Copy template to create .env
cp .env.example .env

# Edit .env and replace:
# OPENAI_API_KEY=sk-your-actual-api-key-here
```

**⚠️ CRITICAL**: The `.env` file is gitignored. You MUST configure it with your actual OpenAI API key:

```
OPENAI_API_KEY=sk-your-real-key-here
```

### Step 3: Frontend Setup

```bash
cd truehire-ai/frontend

# Install dependencies using pnpm
pnpm install
```

### Step 4: Start Backend

From `truehire-ai/backend` (with venv activated):

```bash
python app/main.py
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Test Health Endpoint:**
```bash
curl http://localhost:8000/api/health

# Expected Response:
{"status":"ok","service":"truehire-backend"}
```

### Step 5: Start Frontend (New Terminal)

From `truehire-ai/frontend`:

```bash
pnpm dev
```

**Expected Output:**
```
- ready on http://localhost:3000
```

Open http://localhost:3000 in your browser. You should see:

1. **Title**: "TrueHire AI"
2. **Status Indicator**: 
   - ✅ "Backend connected ✅" (if backend is running)
   - ❌ "Backend not reachable ❌" (if backend is down)

---

## 🔧 Convenient Development Startup

### Option A: Using Root Scripts

From the `truehire-ai` root directory:

**macOS/Linux:**
```bash
chmod +x scripts/dev.sh
./scripts/dev.sh
```

**Windows PowerShell:**
```powershell
.\scripts\dev.ps1
```

This will automatically:
- Create Python venv (if needed)
- Install backend dependencies
- Install frontend dependencies
- Start both servers in background processes

### Option B: Manual (Two Terminals)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # or: venv\Scripts\Activate.ps1
python app/main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
pnpm dev
```

---

## ✅ Verification Checklist

- [ ] Node.js 18+ installed: `node --version`
- [ ] Python 3.11+ installed: `python --version`
- [ ] pnpm installed: `pnpm --version`
- [ ] Backend venv created and activated
- [ ] Backend dependencies installed: `pip install -r requirements.txt`
- [ ] Backend .env configured with OpenAI API key
- [ ] Frontend dependencies installed: `pnpm install`
- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:3000
- [ ] Health endpoint responding: `curl http://localhost:8000/api/health`
- [ ] Frontend shows status indicator in browser

---

## 📁 Key File Locations

### Backend Configuration
- **Main App**: `backend/app/main.py`
- **Settings**: `backend/app/core/config.py` (loads from `.env`)
- **Health Route**: `backend/app/api/routes/health.py`
- **Environment Vars**: `backend/.env` (create from `.env.example`)

### Frontend Configuration
- **Main Page**: `frontend/app/page.tsx`
- **API Client**: `frontend/lib/api.ts`
- **Custom Hook**: `frontend/hooks/useHealthStatus.ts`
- **Environment Vars**: `frontend/.env.local`

### Project Documentation
- **README**: `README.md` (full setup guide)
- **Architecture**: `docs/ARCHITECTURE.md` (design decisions, patterns)

---

## 🐛 Troubleshooting

### "Backend not reachable" on frontend

**Check:**
1. Is backend running on port 8000?
   ```bash
   curl http://localhost:8000/api/health
   ```

2. Is CORS properly configured?
   - Edit `backend/.env`: `ALLOWED_ORIGINS=["http://localhost:3000"]`
   - Restart backend

3. Check browser console for network errors
   - Open DevTools (F12) → Console tab
   - Look for CORS or fetch errors

### Backend fails to start

**Check:**
1. Python version: `python --version` (must be 3.11+)
2. Virtual environment activated: `which python` (should show venv path)
3. Dependencies installed: `pip list | grep fastapi`
4. Port 8000 not in use: `lsof -i :8000` (macOS/Linux)

### Frontend won't start

**Check:**
1. Node version: `node --version` (must be 18+)
2. pnpm installed: `pnpm --version`
3. Dependencies installed: `ls frontend/node_modules` (should exist)
4. Port 3000 not in use: `lsof -i :3000` (macOS/Linux)

---

## 🎯 Next Steps

This foundation is now ready for these upcoming features:

1. **CV Upload & Parsing** — Extract candidate info from PDF/DOC
2. **Interview Question Generation** — Use OpenAI to generate contextual questions
3. **Face Detection** — Detect multiple people, eye movement tracking
4. **Real-time Analysis** — WebSocket communication during interviews
5. **Database Models** — Candidates, interviews, results, analytics
6. **Authentication** — JWT-based user/admin login
7. **Professional UI** — Interview experience, candidate dashboard

---

## 📞 Support Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Next.js Docs**: https://nextjs.org/docs
- **Pydantic**: https://docs.pydantic.dev/
- **Tailwind CSS**: https://tailwindcss.com/docs

---

**Last Updated**: 2025-02-17  
**Status**: ✅ Ready for Development
