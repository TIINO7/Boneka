from io import BytesIO
from typing import List
from sqlalchemy.orm import Session
from database import get_db
from fastapi import APIRouter, Depends, File, HTTPException, HTTPException, UploadFile
from models import  ProfileImage, User
from schemas.supplier_schema import Supplier as SupplierBase, SupplierCreate, SupplierUpdate
from uuid import UUID
from fastapi.responses import StreamingResponse

# Create a new router for users
supplier_router = APIRouter()


# CRUD operations for suppliers
@supplier_router.post("/", response_model=SupplierBase)
def create_supplier(supplier: SupplierCreate, db: Session = Depends(get_db)):
    # Check if the supplier already exists
    existing_supplier = db.query(User).filter(User.email == supplier.email).first()
    if existing_supplier:
        raise HTTPException(status_code=400, detail="Supplier already exists")
    
    # Create a new supplier
    new_supplier = User(
        email=supplier.email,
        name=supplier.name,
        status = "pending",
        phone_number=supplier.phone_number if supplier.phone_number else None,
        latitude=supplier.latitude,
        longitude=supplier.longitude,
        role="supplier"
    )
    db.add(new_supplier)
    db.commit()
    db.refresh(new_supplier)
    
    return new_supplier

@supplier_router.get("/{name}", response_model=SupplierBase)
def get_supplier(name: str, db: Session = Depends(get_db)):
    supplier = db.query(User).filter(User.name == name).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier

# get supplier by id
@supplier_router.get("{user_id}/suplier",response_model=SupplierBase)
def get_supplier_by_id(user_id:UUID, db:Session = Depends(get_db)): 
    supplier = db.query(User).filter(User.id == user_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    return supplier

@supplier_router.put("/{user_id}", response_model=SupplierBase)
def update_supplier(user_id: UUID, supplier: SupplierUpdate, db: Session = Depends(get_db
)):
    existing_supplier = db.query(User).filter(User.id == user_id).first()
    if not existing_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Update supplier details
    existing_supplier.email = supplier.email
    # TODO: verify that the new email address supplied indeed belongs to the user
    existing_supplier.name = supplier.name
    existing_supplier.phone_number = supplier.phone_number 
    existing_supplier.latitude = supplier.latitude
    existing_supplier.longitude = supplier.longitude
    
    db.commit()
    db.refresh(existing_supplier)
    
    return existing_supplier

@supplier_router.delete("/{user_id}", response_model=SupplierBase)
def delete_supplier(user_id:UUID, db: Session = Depends(get_db)):
    supplier = db.query(User).filter(User.id == user_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    db.delete(supplier)
    db.commit()
    
    return supplier

@supplier_router.get("/", response_model=list[SupplierBase])
def get_all_suppliers(db: Session = Depends(get_db)):
    suppliers = db.query(User).filter(User.role == "supplier").all()
    return suppliers

@supplier_router.get("/exists/{email}", response_model=bool)
def supplier_exists(email: str, db: Session = Depends(get_db)):
    supplier = db.query(User).filter(User.email == email).first()
    if supplier is None:
        return False
    else:
        return True
    
# add a profile picture to the suppiler
@supplier_router.post("/image/{user_id}")
async def add_profile_image(user_id:UUID,file: UploadFile = File(...), db:Session = Depends(get_db)):
    supplier = db.query(User).filter(User.id == user_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 1. Read the file contents
    contents = await file.read()       # bytes
    
    # 2. check if user profile alread exists if so then update
    if supplier.profile_image:
        supplier.profile_image.image_data = contents

    else:
    # 3. Create the RequestImage row if it wasnt already created
        img = ProfileImage(
            user_id=supplier.id,
            image_data = contents
        )
    
        db.add(img)
        db.commit()
        db.refresh(img)
    
    db.commit()

    return {"msg": "successful", "image_id": img.id if supplier.profile_image is None else supplier.profile_image.id}
    
#get image of supplier profile
@supplier_router.get("/image/{supplier_id}")
def get_profile_image(supplier_id: UUID, db: Session = Depends(get_db)):
    supplier = db.query(User).filter(User.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not supplier.profile_image:
        raise HTTPException(status_code=404, detail="Profile image not found")
    
    return StreamingResponse(BytesIO(supplier.profile_image.image_data), media_type="image/png")