from fastapi import APIRouter

from app.api.routes import (
    login,
    users,
    institutions,
    job_postings,
    comparisons,
    model_names,
)

api_router = APIRouter()
api_router.include_router(
    model_names.router, prefix="/model_names", tags=["model_names"]
)
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    institutions.router, prefix="/institutions", tags=["institutions"]
)
api_router.include_router(
    job_postings.router, prefix="/job-postings", tags=["job-postings"]
)
api_router.include_router(
    comparisons.router,
    prefix="/comparisons",
    tags=["comparisons"],
)
api_router.include_router(
    model_names.router, prefix="/model-names", tags=["model-names"]
)
