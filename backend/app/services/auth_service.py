from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.merchant import Merchant
from app.models.user import User
from app.schemas.auth import UserRegister
from app.services.audit_service import record_audit_event


def register_user(db: Session, user_in: UserRegister) -> User:
    """Register a new user account."""
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    if user_in.merchant_id:
        merchant = db.query(Merchant).filter(Merchant.id == user_in.merchant_id).first()
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Merchant not found",
            )

    user = User(
        email=user_in.email,
        password_hash=hash_password(user_in.password),
        role=user_in.role,
        merchant_id=user_in.merchant_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    record_audit_event(
        db=db,
        actor_type="USER",
        actor_id=str(user.id),
        action="user_registered",
        resource_type="User",
        resource_id=str(user.id),
        merchant_id=user.merchant_id,
        metadata={"email": user.email, "role": user.role},
    )

    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
        )

    record_audit_event(
        db=db,
        actor_type="USER",
        actor_id=str(user.id),
        action="login_success",
        resource_type="User",
        resource_id=str(user.id),
        merchant_id=user.merchant_id,
        metadata={"email": user.email},
    )

    return user
