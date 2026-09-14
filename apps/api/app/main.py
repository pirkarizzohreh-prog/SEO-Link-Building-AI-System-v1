from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title="SEO Link Building AI Platform API",
    description="Backend for the SEO Link Building AI Platform (Sprint 1: Backend + Database).",
    version="0.1.0",
)

# Permissive in development; tighten to the actual Next.js dashboard origin
# once Sprint 2 (Auth + Dashboard) deploys it.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENV == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
def health() -> dict:
    return {"status": "ok", "env": settings.ENV}


app.include_router(api_router, prefix="/api/v1")
