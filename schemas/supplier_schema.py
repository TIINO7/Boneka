from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class SupplierBase(BaseModel):
    email: EmailStr
    name: str
    phone_number: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
class SupplierCreate(SupplierBase):
    pass
    
class Supplier(SupplierBase):
    id: UUID
    status: str
    role: str 
    created_at: datetime
    
    class Config:
        orm_mode = True

