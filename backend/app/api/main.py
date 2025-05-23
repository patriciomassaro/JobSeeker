from fastapi import APIRouter

from app.api.routes import (
    login,
    users,
    job_postings,
    comparisons,
    dimensions,
)

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    job_postings.router, prefix="/job-postings", tags=["job-postings"]
)
api_router.include_router(
    comparisons.router,
    prefix="/comparisons",
    tags=["comparisons"],
)
api_router.include_router(dimensions.router, prefix="/dimensions", tags=["dimensions"])
