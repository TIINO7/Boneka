from typing import List
from sqlalchemy.orm import Session
from database import get_db
from fastapi import APIRouter, Depends, File, HTTPException, HTTPException, UploadFile
from models import  RequestPost, RequestImage
from schemas.request_schema import RequestCreate, Request as RequestBase, RequestImageRead, RequestUpdate
from uuid import UUID

        
# Create a new router for requesting posts
request_router = APIRouter(prefix="/requests", tags=["requests"])

# CRUD operations for RequestPost

# Create a new request post
@request_router.post("/requests/", response_model=RequestBase)
def create_request(request: RequestCreate, db: Session = Depends(get_db)):
    db_request = RequestPost(
        title = request.title,
        category = request.category,
        description = request.description,
        offer_price = request.offer_price,
        customer_id = request.customer_id
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

# add a picture to the request
@request_router.post("/{request_id}/images/", response_model=RequestImageRead)
async def upload_request_image(
    request_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # 1. Make sure the request exists
    request_obj = db.query(RequestPost).filter_by(id=request_id).first()
    if not request_obj:
        raise HTTPException(status_code=404, detail="Request not found")

    # 2. Read the file contents
    contents = await file.read()       # bytes

    # 3. Create the RequestImage row
    img = RequestImage(
        request_id = request_obj.id,
        image_data = contents
    )
    db.add(img)
    db.commit()
    db.refresh(img)

    return img

# Get all request posts
@request_router.get("/get_all",response_model=List[RequestBase])
async def get_all_requests(db:Session = Depends(get_db)):
    requests = db.query(RequestPost).all()
    return requests

# Get a request by id 
@request_router.get("/get_single/{request_id}",response_model=RequestBase)
async def get_all_requests(request_id:int, db:Session = Depends(get_db)):
    request = db.query(RequestPost).filter(RequestPost.id == request_id).first()
    return request

# get image for a request
@request_router.get("/{request_id}/images/", response_model=List[RequestImageRead])
def list_request_images(
    request_id: UUID,
    db: Session = Depends(get_db),
):
    images = (
        db.query(RequestImage)
          .filter_by(request_id=request_id)
          .all()
    )
    return images


# add get by , title , category

# update a request
@request_router.put("/update/{request_id}", response_model=RequestBase)
async def update_request(requestupdate:RequestUpdate,db:Session= Depends(get_db)):
    #check if the request still exist 
    existing_request = db.query(RequestPost).filter(RequestPost.id == requestupdate.id).first()
    if not existing_request:
        raise HTTPException(status_code=404, detail="request not found")
    
    # update the rows
    try:
        existing_request.title = requestupdate.title
        existing_request.description = requestupdate.description
        existing_request.category = requestupdate.category
        existing_request.offer_price = requestupdate.offer_price
        
        db.commit()
        db.refresh(existing_request)
        return existing_request
    except:
        db.rollback()
        raise HTTPException(status_code=500,detail="internal error")

# Delete a request
@request_router.delete("/delete/{request_id}")
def delete_request(request_id:UUID, db:Session = Depends(get_db)):
      #check if the request still exist 
    existing_request = db.query(RequestPost).filter(RequestPost.id == request_id).first()
    if not existing_request:
        raise HTTPException(status_code=404, detail="request not found")
    
    db.delete(existing_request)
    db.commit()
    return {"msg" : "request deleted sucessfully"}

# add auto delete capabilities for requests older than 7 days
