from typing import Optional
from sqlalchemy.orm import Session
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from models import User
from schemas.auth_schema import AuthBase as AuthCreate, AuthResponse, PasswordChange, PasswordResetRequest
import bcrypt
from uuid import UUID
import string
import secrets

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies if a given password matches the stored hash."""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

# Hash password
def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)
    return hashed_password.decode()

def create_reset_pin(length: int = 8) -> str:
    """
    Generate a random OTP (one‑time password) consisting of uppercase letters,
    lowercase letters, and digits.

    :param length: The length of the OTP to generate (default: 8)
    :return: A securely generated random string of the given length.
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def authenticate_user(db: Session,  password: str, user_id) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


# Create a new router for users
auth_router = APIRouter(prefix="/auth",tags=["Auth"])

# add password to a user and change status to active
@auth_router.post("/create_password", response_model=AuthResponse)
def add_password(auth:AuthCreate , db:Session = Depends(get_db)):
    # check if the user exists 
    user = db.query(User).filter(User.id == auth.user_id).first()
    
    if not user :
        raise HTTPException(status_code=404, detail="user not found")
    
    #if user exist add password and change status
    hash_pass = hash_password(auth.password)
    
    user.password_hash = hash_password
    user.status = "active"
    db.commit()
    db.refresh(user)
    return user


@auth_router.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if user:
        # generate reset password and send email
        reset_token = create_reset_pin()
        user.password_hash = hash_password(reset_token)
        print(reset_token)
        # TODO: send email with the new password
    return


# Endpoints
@auth_router.post("/access", response_model=AuthResponse)
async def login(form_data: AuthCreate, db: Session = Depends(get_db)):
    user = authenticate_user(db,form_data.password,form_data.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    return user


@auth_router.post("/change-password")
async def change_password(data: PasswordChange, db: Session = Depends(get_db)):
    
    #verify if the current password matches with the one supplied from the user
    user = authenticate_user(db,data.old_password,data.user_id)
    
    if not user:
        raise HTTPException(
            status_code=505,
            detail="incorrect password"
        )
        
    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"msg":"succesful"}


