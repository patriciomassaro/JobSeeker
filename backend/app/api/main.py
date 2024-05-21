from fastapi import APIRouter

from app.api.routes import (
    login,
    users,
    institutions,
    job_postings,
    user_job_posting_comparisons,
)

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    institutions.router, prefix="/institutions", tags=["institutions"]
)
api_router.include_router(
    job_postings.router, prefix="/job_postings", tags=["job_postings"]
)
api_router.include_router(
    user_job_posting_comparisons.router,
    prefix="/user_job_posting_comparisons",
    tags=["user_job_posting_comparisons"],
)
