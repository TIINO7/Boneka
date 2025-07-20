from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, Numeric,UniqueConstraint, String, Text, Date, Float, ForeignKey, LargeBinary, event, func, text
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid



class User(Base):
    __tablename__ = "users"
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username   = Column(String, nullable=True)
    role       = Column(Enum("customer","supplier","admin", name="user_roles"), nullable=False)
    name       = Column(String, nullable=False)
    surname    = Column(String, nullable=True) 
    phone_number = Column(String, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String) # male or female
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status     = Column(Enum("active",
                            "disabled",
                            "pending",
                            name="user_statuses"),
                            server_default="active", nullable=False)
    latitude  = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    #relationships
    requests = relationship("RequestPost", back_populates="customer", cascade="all, delete")
    offers = relationship("Offer", back_populates="supplier", cascade="all, delete")
    profile_image = relationship("ProfileImage", back_populates="user", uselist=False, cascade="all, delete")
    products = relationship("Product", back_populates="supplier", cascade="all, delete")
    customer_orders = relationship("Order", foreign_keys="[Order.customer_id]", back_populates="customer")
    supplier_orders = relationship("Order", foreign_keys="[Order.supplier_id]", back_populates="supplier")



class RequestPost(Base):
    __tablename__ = "request_posts"
    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text)
    category = Column(Text)
    offer_price = Column(Numeric(12,2))
    quantity = Column(Integer, default=1)
    status = Column(
        Enum("open","accepted","declined","cancelled", name="request_statuses"),
        server_default="open",
        nullable=False,
    )
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    customer = relationship("User", back_populates="requests")
    offers = relationship("Offer", back_populates="request", cascade="all, delete")
    images = relationship("RequestImage", back_populates="request", cascade="all, delete")
    
    
class RequestImage(Base):
    __tablename__ = "request_images"
    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(Integer, ForeignKey("request_posts.id"))
    image_data = Column(LargeBinary, nullable=False)
    
    request = relationship("RequestPost", back_populates="images")
    
class Offer(Base):
    __tablename__ = "offers"
    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("request_posts.id"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    proposed     = Column(Numeric(12,2), nullable=False)
    status       = Column(Enum("pending","accepted","rejected", name="offer_statuses"),
                        server_default="pending", nullable=False)
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    request = relationship("RequestPost", back_populates="offers")
    supplier = relationship("User", back_populates="offers")
    
class Product(Base):
    __tablename__ = "products"
    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    description = Column(Text)
    category = Column(String, nullable=False) # e.g. electronics, furniture, etc.
    price = Column(Numeric(12,2), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    supplier = relationship("User", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete")


class ProductImage(Base):
    __tablename__ = "product_images"
    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    image_data = Column(LargeBinary, nullable=False)
        
    product = relationship("Product", back_populates="images")

# class for profile images for both users and suppliers
class ProfileImage(Base):
    __tablename__ = "profile_images"
    id      = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    image_data = Column(LargeBinary, nullable=False)

    user = relationship("User", back_populates="profile_image", uselist=False)
    
    
# auth models 
class DeviceToken(Base):
    __tablename__ = "device_tokens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    device_id = Column(String, nullable=False)  # provided by the app
    token = Column(String, unique=True, nullable=False)
    issued_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_used = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False)


# orders for supplier
class Order(Base):
    __tablename__ = "orders"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    request_id = Column(UUID(as_uuid=True), ForeignKey("request_posts.id"), nullable=False)
    offer_id = Column(UUID(as_uuid=True), ForeignKey("offers.id"), nullable=False)

    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    status = Column(Enum("placed", "delivered", "cancelled", name="order_statuses"),
                    server_default="placed", nullable=False)

    total_price = Column(Numeric(12, 2), nullable=False)
    quantity = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    request = relationship("RequestPost")
    offer = relationship("Offer")
    customer = relationship("User", foreign_keys=[customer_id], back_populates="customer_orders")
    supplier = relationship("User", foreign_keys=[supplier_id], back_populates="supplier_orders")
