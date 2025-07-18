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
    db_product = Product(
        name = product.name,
        description = product.description,
        price = product.price,
        category = product.category,
        supplier_id = product.supplier_id
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@product_router.post("/{product_id}/images")
async def add_product_images(
    product_id: UUID,
    file: UploadFile = File(...),  # required
    db: Session = Depends(get_db)
):
    """
    add up to 4 images for a product 
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

    #check if the amount of images for a product have reached the maximum allowed 4
    
    image_count = db.query(ProductImage).filter(ProductImage.product_id == db_product.id).count()
    if image_count >= 4:
        raise HTTPException(status_code=500 , detail="upload amount reachecd")
    # Read file1
    contents = await file.read()
    new_image = ProductImage(
        product_id=product_id,
        image_data=contents
    )
    db.add(new_image)
    db.commit()
    db.refresh(new_image)

    return {"msg": "successful",
            "image_id1": new_image.id}
    

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

@product_router.get("/images/{image_id}")
def get_product_image(
    image_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Stream back the stored image blobs.

    """
    img: ProductImage | None = (
        db.query(ProductImage)
        .filter(ProductImage.id == image_id)
        .first()
    )
    if not img:
        raise HTTPException(404, "Image not found")

    data = img.image_data
    
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

@product_router.get("/supplier/{supplier_id}/count")
def count_products_by_supplier(supplier_id: UUID, db: Session = Depends(get_db)):
    count = db.query(Product).filter(Product.supplier_id == supplier_id).count()
    return count

@product_router.get("/count")
def count_all_products(db: Session = Depends(get_db)):
    count = db.query(Product).count()
    return count

