import datetime
from decimal import Decimal
from pydantic import BaseModel
from typing import Literal, Optional
from uuid import UUID

class OrderAction(BaseModel):
    user_id: UUID
    order_id: UUID
    action: Literal["delivered", "cancelled"]

class RequestInfo(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    category: Optional[str]

    model_config = {
        "from_attributes": True 
    }

class OrderOut(BaseModel):
    id: UUID
    status: str
    total_price: Decimal
    quantity: int
    created_at: datetime.datetime  
    request: RequestInfo

    model_config = {
        "from_attributes": True  
    }
