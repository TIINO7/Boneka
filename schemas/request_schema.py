import datetime
from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class RequestBase(BaseModel):
    title: str
    category: str
    quantity:Optional[int] = 1
    description : Optional[str] = None
    offer_price : float
    customer_id: UUID
    
class RequestCreate(RequestBase):
    pass

class RequestUpdate(RequestBase):
    id : UUID 
        
class Request(RequestBase):
    id: UUID
    created_at: datetime.datetime    
    
    class Config:
        orm_mode = True



class RequestImageRead(BaseModel):
    id: UUID
    request_id: UUID

    class Config:
        orm_mode = True
