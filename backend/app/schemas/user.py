"""User-related request/response schemas."""
from pydantic import BaseModel, EmailStr, constr


class RegisterUserRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=6)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: str

    class Config:
        orm_mode = True
