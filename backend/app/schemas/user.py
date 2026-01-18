"""User-related request/response schemas.

EmailStr requires an extra dependency (`email-validator`). To keep the
development environment minimal, use a constrained string for emails.
Replace with `constr` and a minimal length requirement; production should
use proper email validation.
"""
from pydantic import BaseModel, constr


Email = constr(min_length=5)


class RegisterUserRequest(BaseModel):
    email: Email
    password: constr(min_length=6)


class LoginRequest(BaseModel):
    email: Email
    password: constr(min_length=6)


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: str

    class Config:
        from_attributes = True
