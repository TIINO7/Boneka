from io import BytesIO
from typing import Optional
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from fastapi import APIRouter, Depends, File, HTTPException, HTTPException, UploadFile
from models import Product , User, ProductImage
from schemas.products_schema import Product as ProductBase, ProductCreate
from uuid import UUID


# Create a new router for users
product_router = APIRouter()

#crud operations for products
@product_router.post("/", response_model=ProductBase)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@product_router.post("/{product_id}/images", response_model=ProductBase)
async def add_product_images(
    product_id: UUID,
    file: UploadFile = File(...),  # required
    file2: Optional[UploadFile] = File(None),  # optional
    file3: Optional[UploadFile] = File(None),  # optional
    db: Session = Depends(get_db)
):
    """
    add up to 3 product images 

    Args:
        product_id (UUID): _description_
        file (UploadFile, optional): _description_. Defaults to File(...).

    Raises:
        HTTPException: _description_

    Returns:
        _type_: _description_
    """
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Read file1
    contents = await file.read()
    new_image = ProductImage(
        product_id=product_id,
        image_data=contents
    )
    db.add(new_image)
    
    # Read optional file2
    if file2:
        contents2 = await file2.read()
        new_image2 = ProductImage(
        product_id=product_id,
        image_data=contents2
    )
        db.add(new_image2)

    # Read optional file3
    if file3:
        contents3 = await file3.read()
        new_image3 = ProductImage(
        product_id=product_id,
        image_data=contents3
    )
        db.add(new_image3)

    db.commit()
    db.refresh(new_image)
    if new_image2 :
        db.refresh(new_image2) 
    if new_image3:
        db.refresh(new_image3)

    return {"msg": "successful",
            "image_id1": new_image.id,
            "image_id2": new_image2.id if new_image2 else None,
            "image_id3": new_image2.id if new_image3 else None}
    

@product_router.get("/{product_id}/images", response_model=list[UUID])
def list_product_images(product_id: UUID, db: Session = Depends(get_db)):
    """
    Return a list of ProductImage IDs for this product.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")

    images = db.query(ProductImage).filter(ProductImage.product_id == product_id).all()
    return [img.id for img in images]

@product_router.get("/{product_id}/images/{image_id}")
def get_product_image(
    product_id: UUID,
    image_id: UUID,
    slot: int = 1,  # choose which file field: 1, 2 or 3
    db: Session = Depends(get_db)
):
    """
    Stream back the stored image blobs.

    """
    img: ProductImage | None = (
        db.query(ProductImage)
        .filter(ProductImage.id == image_id, ProductImage.product_id == product_id)
        .first()
    )
    if not img:
        raise HTTPException(404, "Image not found")

    data = img.image_data
    
    if not data:
        raise HTTPException(404, f"No data in image slot {slot}")

    # return raw bytes as image/jpeg (or you can detect/parameterize the MIME-type)
    return StreamingResponse(BytesIO(data), media_type="image/jpeg")


@product_router.get("/{product_id}", response_model=ProductBase)
def get_product(product_id: UUID, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

#get all products
@product_router.get("/", response_model=list[ProductBase])
def get_all_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products

@product_router.put("/{product_id}", response_model=ProductBase)
def update_product(product_id: UUID, product: ProductCreate, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for key, value in product.dict().items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

@product_router.delete("/{product_id}")
def delete_product(product_id: UUID, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(db_product)
    db.commit()
    return {"detail": "Product deleted successfully"}

@product_router.get("/supplier/{supplier_id}", response_model=list[ProductBase])
def get_products_by_supplier(supplier_id: UUID, db: Session = Depends(get_db)):
    db_supplier = db.query(User).filter(User.id == supplier_id).first()
    if not db_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    products = db.query(Product).filter(Product.supplier_id == supplier_id).all()
    return products

@product_router.get("/category/{category}", response_model=list[ProductBase])
def get_products_by_category(category: str, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.category == category).all()
    if not products:
        raise HTTPException(status_code=404, detail="No products found in this category")
    return products

@product_router.get("/search/{query}", response_model=list[ProductBase])
def search_products(query: str, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.name.ilike(f"%{query}%")).all()
    if not products:
        raise HTTPException(status_code=404, detail="No products found matching the query")
    return products

@product_router.get("/supplier/{supplier_id}/count", response_model=int)
def count_products_by_supplier(supplier_id: UUID, db: Session = Depends(get_db)):
    count = db.query(Product).filter(Product.supplier_id == supplier_id).count()
    return count

@product_router.get("/count", response_model=int)
def count_all_products(db: Session = Depends(get_db)):
    count = db.query(Product).count()
    return count

