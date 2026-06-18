"""FastAPI application factory and entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, create_engine

from app.core.config import settings
from app.api.routes import health, cv, interview, identity, demo


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        debug=settings.debug,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Create database tables
    engine = create_engine(settings.database_url)
    SQLModel.metadata.create_all(engine)
    
    # Include routers
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(cv.router, prefix="/api/cv", tags=["cv"])
    app.include_router(interview.router, prefix="/api/interview", tags=["interview"])
    app.include_router(identity.router, prefix="/api/identity", tags=["identity"])
    app.include_router(demo.router, prefix="/api/demo", tags=["demo"])
    
    return app


# Application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
