from fastapi import FastAPI

from bgv_app.config import get_settings
from bgv_app.database import init_db
from bgv_app.routes import agentic_bgv, analysis, bgv, candidates

settings = get_settings()
app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/")
def health():
    return {"status": "ok", "app": settings.app_name}


app.include_router(candidates.router)
app.include_router(agentic_bgv.router)
app.include_router(analysis.router)
app.include_router(bgv.router)
