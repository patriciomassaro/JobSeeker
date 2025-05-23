from typing import Any
from sqlmodel import Session, select


from app.core.security import get_password_hash, verify_password
from app.models import (
    Users,
    UserCreate,
    UserUpdateMe,
    BalanceTransactions,
    BalanceTransactionsTypeEnum,
)
from app.logger import Logger


logger = Logger(prefix="UsersCRUD", log_file_name="crud.log").get_logger()


def create_user(
    *, session: Session, user_create: UserCreate, is_superuser: bool = False
) -> Users:
    db_obj = Users.model_validate(
        user_create,
        update={
            "password": get_password_hash(user_create.password),
            "is_superuser": is_superuser,
        },
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    logger.info(f"User {db_obj.username} created successfully")
    return db_obj


def add_balance_to_user(session: Session, user: Users, amount: float):
    transaction = BalanceTransactions(
        user_id=user.id,  # type: ignore
        amount=amount,
        transaction_type_id=BalanceTransactionsTypeEnum.DEPOSIT.value[0],
    )
    user.balance += amount
    session.add(transaction)
    session.commit()
    logger.info(f"User {user.id} added {amount} to balance successfully")


def update_user(*, session: Session, db_user: Users, user_in: UserUpdateMe) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    logger.info(f"User {db_user.username} updated successfully")
    return db_user


def get_user_by_username(*, session: Session, username: str) -> Users | None:
    statement = select(Users).where(Users.username == username)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, username: str, password: str) -> Users | None:
    db_user = get_user_by_username(session=session, username=username)
    if not db_user:
        return None
    if not verify_password(password, db_user.password):
        return None
    return db_user
