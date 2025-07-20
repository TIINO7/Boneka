from typing import List
from sqlalchemy.orm import Session
from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from models import Offer, Order, RequestPost, User
from uuid import UUID
from schemas.orders_schema import OrderAction, OrderOut

# Create a new router for users
orders_router = APIRouter(prefix="/orders", tags=["orders"])

#get all orders that havent been  for a user (customer and supplier)
@orders_router.get("/get_order/{user_id}")
def get_all_orders(user_id:UUID,db:Session=Depends(get_db)):
    orders = db.query(Order).filter(Order.customer_id == user_id or Order.supplier_id == user_id,
                                    Order.status == "placed").all()
    return orders

# mark order as delivered or as cancelled 
@orders_router.post("/mark_order")
def mark_order(action:OrderAction,db:Session=Depends(get_db)):
    order = db.query(Order).filter(Order.id == action.order_id).first()
    if not order:
        raise HTTPException(status_code=404,detail="order not found")
    #check to see if user is the customer or supplier and apply action accordingly
    user = db.query(User).filter(User.id == action.user_id).first()
    if user.role == "customer" and action.action == "cancelled":
        order.status = "cancelled"
        
    elif user.role == "supplier" and action.action == "delivered":
        order.status = "deliverd"
    else:
        raise HTTPException(status_code=500 ,detail="User not allowed to perform this action")
    
    db.commit()
    return {"msg": "order status updated successfully"}

# get all delivered orders , can be used as history
@orders_router.get("/completed_orders", response_model=list[OrderOut])
def get_all_completed_orders(user_id: UUID, db: Session = Depends(get_db)):
    orders = (
        db.query(Order)
        .filter(Order.status == "delivered", Order.customer_id == user_id)
        .all()
    )
    return orders