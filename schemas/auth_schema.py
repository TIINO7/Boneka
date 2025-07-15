from pydantic import BaseModel, EmailStr
from typing import Literal, Optional
from datetime import datetime
from uuid import UUID


class AuthBase(BaseModel):
    user_id : UUID
    password : str
    

class AuthResponse(BaseModel):
    user_id : UUID
    status : str
    role : str
    
class PasswordResetRequest(BaseModel):
    email: str
    
class PasswordChange(BaseModel):
    user_id : UUID
    old_password : str
    new_password : str