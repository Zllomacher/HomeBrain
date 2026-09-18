from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import BASE_DIR, settings
from backend.database import init_db
from backend.routers import auth_router, documents_router, settings_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and seed initial users on startup
    init_db()
    yield

app = FastAPI(
    title="HomeBrain API",
    description="Backend pro správu rodinných dokumentů, účtenek a smluv",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router.router)
app.include_router(settings_router.router)
app.include_router(documents_router.router)

# Mount Frontend Static Files
frontend_dir = BASE_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
