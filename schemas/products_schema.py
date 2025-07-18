from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class ProductBase(BaseModel):
    name: str
    description : Optional[str] = None
    price : float
    supplier_id: UUID    
    category: str  # e.g. electronics, furniture, etc.
    
class ProductCreate(ProductBase):
    pass
    
class Product(ProductBase):
    id: UUID
    
    class Config:
        orm_mode = True
        