from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title="SEO Link Building AI Platform API",
    description="Backend for the SEO Link Building AI Platform (Sprint 1: Backend + Database).",
    version="0.1.0",
)

# The dashboard sends its access token as an Authorization header, never a
# cookie, so allow_credentials stays False — which is what makes a
# wildcard origin in development safe/spec-compliant in the first place
# (browsers reject `*` together with credentialed requests). In
# production, only the configured FRONTEND_ORIGINS are allowed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENV == "development" else settings.FRONTEND_ORIGINS.split(","),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
def health() -> dict:
    return {"status": "ok", "env": settings.ENV}


app.include_router(api_router, prefix="/api/v1")
