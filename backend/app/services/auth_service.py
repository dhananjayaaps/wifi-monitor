"""Authentication and user management services."""
from typing import Optional
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import User


class AuthError(Exception):
    pass


def register_user(email: str, password: str) -> User:
    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise AuthError("Email already registered") from exc
    return user


def authenticate(email: str, password: str) -> Optional[str]:
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise AuthError("Invalid credentials")
    token = create_access_token(identity=str(user.id))
    return token


def get_user(user_id: int) -> Optional[User]:
    return User.query.get(user_id)
