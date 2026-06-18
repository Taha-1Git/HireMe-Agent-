# TrueHire AI Development Script (Windows PowerShell)
# Starts both frontend and backend servers

Write-Host "🚀 Starting TrueHire AI development servers..." -ForegroundColor Green
Write-Host ""

# Function to start backend
function Start-Backend {
    Write-Host "📦 Starting backend (FastAPI)..." -ForegroundColor Blue
    
    Push-Location backend
    
    # Check if venv exists, if not create it
    if (!(Test-Path "venv")) {
        Write-Host "⚠️  Virtual environment not found. Creating it now..." -ForegroundColor Yellow
        python -m venv venv
        & ".\venv\Scripts\Activate.ps1"
        pip install -r requirements.txt
    } else {
        & ".\venv\Scripts\Activate.ps1"
    }
    
    Start-Process -NoNewWindow -FilePath "python" -ArgumentList "app/main.py"
    Write-Host "✅ Backend started on http://localhost:8000" -ForegroundColor Green
    
    Pop-Location
}

# Function to start frontend
function Start-Frontend {
    Start-Sleep -Seconds 2
    
    Write-Host "⚛️  Starting frontend (Next.js)..." -ForegroundColor Blue
    
    Push-Location frontend
    
    # Check if node_modules exists
    if (!(Test-Path "node_modules")) {
        Write-Host "⚠️  Dependencies not found. Installing with pnpm..." -ForegroundColor Yellow
        pnpm install
    }
    
    Start-Process -NoNewWindow -FilePath "pnpm" -ArgumentList "dev"
    Write-Host "✅ Frontend started on http://localhost:3000" -ForegroundColor Green
    
    Pop-Location
}

# Start both servers
Start-Backend
Start-Frontend

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "🎉 Both servers are running!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Frontend:  http://localhost:3000"
Write-Host "📍 Backend:   http://localhost:8000"
Write-Host "📍 Health:    http://localhost:8000/api/health"
Write-Host ""
Write-Host "You can now close this window or press Ctrl+C to stop the servers."
Write-Host ""
