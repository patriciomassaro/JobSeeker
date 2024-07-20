from functools import wraps
from fastapi import HTTPException
from app.api.deps import CurrentUser, SessionDep
from app.models import Users


def require_positive_balance():
    def decorator(func):
        @wraps(func)
        async def wrapper(
            *args, current_user: CurrentUser, session: SessionDep, **kwargs
        ):
            user = session.get(Users, current_user.id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            if user.balance <= 0:
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient balance to perform this operation",
                )
            return await func(
                *args, current_user=current_user, session=session, **kwargs
            )

        return wrapper

    return decorator
