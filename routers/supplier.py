from typing import List
from sqlalchemy.orm import Session
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, HTTPException
from models import  User
from schemas.supplier_schema import Supplier as SupplierBase, SupplierCreate


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

@supplier_router.put("/{email}", response_model=SupplierBase)
def update_supplier(email: str, supplier: SupplierCreate, db: Session = Depends(get_db
)):
    existing_supplier = db.query(User).filter(User.email == email).first()
    if not existing_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Update supplier details
    existing_supplier.email = supplier.email
    existing_supplier.name = supplier.name
    existing_supplier.phone_number = supplier.phone_number if supplier.phone_number else None
    existing_supplier.latitude = supplier.latitude
    existing_supplier.longitude = supplier.longitude
    
    db.commit()
    db.refresh(existing_supplier)
    
    return existing_supplier

@supplier_router.delete("/{email}", response_model=SupplierBase)
def delete_supplier(email: str, db: Session = Depends(get_db)):
    supplier = db.query(User).filter(User.email == email).first()
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
    
