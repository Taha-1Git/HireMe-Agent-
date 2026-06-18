# TrueHire AI — Architecture & Design

## System Overview

TrueHire AI is built as a monorepo with clear separation between frontend (Next.js) and backend (FastAPI). The architecture supports real-time communication, identity verification, and behavioral analysis for AI-powered reverse interviews.

## Directory Structure

### Frontend (`/frontend`)

```
app/                  # Next.js App Router
├── layout.tsx       # Root layout with metadata
├── page.tsx         # Landing page with health status
└── ...              # Future pages (interview, results, etc.)

components/         # React components
├── ui/              # shadcn/ui components (to be added as needed)
└── ...              # Custom components

hooks/              # Custom React hooks
└── useHealthStatus.ts   # Backend connection hook

lib/                # Utilities and helpers
├── api.ts           # API client functions
└── types.ts         # TypeScript type definitions

styles/             # CSS files
└── globals.css      # Tailwind directives and globals
```

**Design Patterns:**
- **API Client**: Centralized in `lib/api.ts` for all backend communication
- **Hooks**: Custom hooks encapsulate frontend logic (e.g., `useHealthStatus`)
- **Components**: Reusable, composable components with Framer Motion animations
- **Types**: All API responses and internal types in `lib/types.ts`

### Backend (`/backend`)

```
app/
├── main.py              # FastAPI app factory, entry point
│
├── api/
│   └── routes/
│       ├── health.py    # Health check endpoint
│       ├── cv.py        # CV parsing endpoints (future)
│       ├── interview.py # Interview endpoints (future)
│       └── auth_guard.py # Authentication endpoints (future)
│
├── core/
│   ├── config.py        # Settings (Pydantic), environment loading
│   └── security.py      # Security utilities, JWT helpers (future)
│
├── models/              # SQLModel database models
│   └── (to be added)
│
├── schemas/             # Pydantic request/response schemas
│   └── (to be added)
│
└── services/            # Business logic layer
    └── (to be added)
```

**Design Patterns:**
- **Configuration**: All env vars loaded via `core/config.py` (Pydantic Settings v2)
- **Routing**: One file per resource for clean separation
- **Services**: Business logic kept in `services/` (not in route files)
- **Schemas**: Pydantic models define request/response contracts
- **Models**: SQLModel defines database tables and ORM entities

## Technology Decisions

### Frontend

| Technology | Why |
|-----------|-----|
| Next.js 14 | Modern React framework with App Router, built-in optimization |
| TypeScript | Type safety for complex state and API contracts |
| Tailwind CSS | Utility-first CSS for rapid, consistent styling |
| Framer Motion | Smooth animations for professional feel |
| lucide-react | Clean, customizable icons |
| shadcn/ui | Copy-paste UI components; full control over styling |

### Backend

| Technology | Why |
|-----------|-----|
| FastAPI | Modern, fast, automatic OpenAPI docs, async support |
| Uvicorn | ASGI server, WebSocket support for real-time features |
| Pydantic v2 | Robust validation and serialization |
| pydantic-settings | Type-safe environment configuration |
| SQLModel | Combines Pydantic and SQLAlchemy for simplicity |
| SQLite | File-based database for dev; easy to replace with PostgreSQL |

## Communication Flow

### Health Check (MVP Vertical Slice)

```
1. Frontend mounts → calls useHealthStatus hook
2. Hook fetches GET /api/health from backend
3. Backend returns {"status": "ok", "service": "truehire-backend"}
4. Frontend shows "Backend connected ✅" or "❌" based on response
```

### CORS Configuration

- **Frontend**: `http://localhost:3000`
- **Backend**: Configured in `app/main.py` with `CORSMiddleware`
- **Origins**: Set in `backend/.env` via `ALLOWED_ORIGINS`

## Environment & Configuration

### Backend Configuration

All settings load from `backend/.env` through `app/core/config.py`:

```python
from app.core.config import settings

# Usage:
settings.api_title        # "TrueHire AI Backend"
settings.allowed_origins  # ["http://localhost:3000"]
settings.openai_api_key   # Environment variable
```

### Frontend Configuration

Environment variables prefixed with `NEXT_PUBLIC_` are exposed to the browser:

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
```

## Development Workflow

### Adding a New API Endpoint

1. **Create schema** in `backend/app/schemas/` (Pydantic models)
2. **Create route** in `backend/app/api/routes/` (one file per feature)
3. **Add business logic** in `backend/app/services/`
4. **Register in `main.py`** with `app.include_router()`
5. **Call from frontend** using `lib/api.ts` client

### Adding a New Frontend Page

1. **Create page** in `app/[route]/page.tsx`
2. **Create components** in `components/`
3. **Add API calls** in `lib/api.ts`
4. **Use hooks** for state management (`useHealthStatus`, etc.)

## WebSocket Support (Future)

FastAPI natively supports WebSockets. When implementing real-time interview updates:

```python
@app.websocket("/ws/interview/{interview_id}")
async def websocket_endpoint(websocket: WebSocket, interview_id: str):
    await websocket.accept()
    # Handle real-time communication
```

## Security Considerations

### Current Phase (MVP)
- CORS enabled only for localhost
- No authentication implemented yet
- OpenAI API key stored in `.env` (gitignored)

### Future Enhancements
- JWT-based authentication
- Role-based access control (RBAC)
- HTTPS in production
- Rate limiting
- Input validation (already in place via Pydantic)

## Deployment Considerations

### Frontend
- Deploy to **Vercel** (Next.js native), **Netlify**, or **AWS Amplify**
- Environment: `NEXT_PUBLIC_API_URL` → production backend URL

### Backend
- Deploy to **Heroku**, **Railway**, **AWS**, or **GCP**
- Environment: All `.env` vars passed as config
- Database: Migrate from SQLite to **PostgreSQL** in production
- Monitoring: Add logging, error tracking (Sentry, etc.)

## Testing Strategy

### Backend Tests
- Unit tests in `app/tests/`
- Use `pytest` for testing
- Mock services and database calls

### Frontend Tests
- Component tests with `@testing-library/react`
- E2E tests with **Playwright** or **Cypress**
- API client tests with `jest-mock-fetch`

## Performance & Optimization

### Frontend
- **Code splitting**: Next.js automatic
- **Image optimization**: `next/image`
- **Font optimization**: Next.js font loader
- **Analytics**: Ready for integration (Vercel Analytics, etc.)

### Backend
- **Async/await**: FastAPI's async support for non-blocking I/O
- **Database indexing**: Add indexes on frequently queried fields
- **Caching**: Redis for session/temporary data (future)
- **Rate limiting**: Implement per user/IP (future)

---

**Last Updated**: 2025-02-17  
**Next Review**: When interview logic begins
