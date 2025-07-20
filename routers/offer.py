from typing import List
from sqlalchemy.orm import Session
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, HTTPException
from models import Offer, Order, RequestPost, User
from schemas.offer_schema import OfferAction, OfferCreate, OfferRead, RequestRead,OfferAccept
from uuid import UUID

        
# Create a new router for users
offer_router = APIRouter(prefix="/offers", tags=["offers"])


# fetch all the requests that a supplier can respond to
@offer_router.get("/requests/{supplier_id}")
def get_requests_for_supplier(
    supplier_id: UUID ,
    db: Session = Depends(get_db),
):
    current_user = db.query(User).filter(User.id == supplier_id).first()
    # pull the supplier’s categories
    categories = {p.category for p in current_user.products}
    # find all open requests matching those categories
    return (
        db.query(RequestPost)
          .filter(RequestPost.status == "open")
          .filter(RequestPost.category.in_(categories))
          .all()
    )


# creating a counter offer
@offer_router.post("/{request_id}/", response_model=OfferRead)
def make_offer(
    request_id: UUID,
    offer_in: OfferCreate,
    db: Session = Depends(get_db)
):
    req = db.query(RequestPost).filter_by(id=request_id, status="open").first()
    if not req:
        raise HTTPException(404, "Request not found or not open")
    current_user = db.query(User).filter(User.id == offer_in.supplier_id).first()
    # ensure supplier actually has a matching product (optional)
    if req.category not in {p.category for p in current_user.products}:
        raise HTTPException(403, "You don’t carry that category")

    offer = Offer(
        request_id = req.id,
        supplier_id = current_user.id,
        proposed    = offer_in.proposed,
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer

# list all offers for a request to a customer 
@offer_router.get("/requests/{request_id}/offers/", response_model=List[OfferRead])
def list_offers(
    request_id: UUID,
    db: Session = Depends(get_db),
):
    req = db.query(RequestPost).filter_by(id=request_id).first()
    if not req:
        raise HTTPException(404, "Not your request or doesn’t exist")
    return req.offers


#Accept / decline a specific offer

# verify this sketchy logic i just wrote
@offer_router.patch("/offers/{offer_id}/")
def respond_to_offer(
    offer_id: UUID,
    action: OfferAction,
    db: Session = Depends(get_db),
):
    """_summary_
    Used by the customer to accept an offer and create an order
    Args:
        offer_id (UUID): _description_
        action (OfferAction): _description_
        db (Session, optional): _description_. Defaults to Depends(get_db).

    Raises:
        HTTPException: _description_
        HTTPException: _description_

    Returns:
        _type_: _description_
    """

    offer = (
        db.query(Offer)
          .join(RequestPost)
          .filter(Offer.id == offer_id)
          .filter(RequestPost.customer_id == action.customer_id)
          .first()
    )
    if not offer:
        raise HTTPException(404, "Offer not found or not yours")
    if offer.status != "pending":
        raise HTTPException(400, "Offer already responded to")

    offer.status = "accepted" if action.action == "accept" else "rejected"
    # if accepted, you may also want to close the request:
    if action.action == "accept":
        offer.request.status = "accepted"
        
        #create an order if the requested is accepted by the customer
        order = Order(
            request_id = offer.request.id,
            offer_id = offer.id,
            customer_id = offer.request.customer_id,
            supplier_id = offer.supplier_id,
            status = "placed",
            total_price = offer.proposed,
            quanity = offer.request.quantity
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return order
    else:
        db.commit()
        return {"msg":"offer rejected"}

# accept offer at face value
@offer_router.post("/accept_request/")
def accept_request(offer: OfferAccept,
                   db:Session=Depends(get_db)):
    """_summary_

    Args:
        offer (OfferAccept): _description_
        db (Session, optional): _description_. Defaults to Depends(get_db).

    Raises:
        HTTPException: _description_
        HTTPException: _description_

    Returns:
        _type_: _description_
    """
    req = db.query(RequestPost).filter_by(id=offer.request_id, status="open").first()
    if not req:
        raise HTTPException(404, "Request not found or not open")
    current_user = db.query(User).filter(User.id == offer.supplier_id).first()
    # ensure supplier actually has a matching product (optional)
    if req.category not in {p.category for p in current_user.products}:
        raise HTTPException(403, "You don’t carry that category")

    offer = Offer(
        request_id  = req.id,
        supplier_id = current_user.id,
        proposed    = req.offer_price,
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer    
