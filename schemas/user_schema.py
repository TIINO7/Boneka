from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

class UserBase(BaseModel):
    email: EmailStr
    date_of_birth: Optional[date] = None
    name : str
    surname : str
    phone_number: Optional[str] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: UUID
    username: str
    status: str
    role: str
    
    class Config:
        orm_mode = True