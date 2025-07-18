from io import BytesIO
from typing import List
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from fastapi import APIRouter, Depends, File, HTTPException, HTTPException, UploadFile
from models import User,ProfileImage
from schemas.user_schema import User as UserBase , UserCreate
from uuid import UUID



        
# Create a new router for users
user_router = APIRouter()

# function to create a username from name and surname
def create_username(name: str, surname: str) -> str:
    """Creates a username by combining name and surname."""
    # Remove spaces and convert to lowercase
    username = f"{name.lower()}.{surname.lower()}"
    return username

# Endpoint to create a new user
@user_router.post("/", response_model=UserBase)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if the user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="credentials already exist")
    
    username = create_username(user.name, user.surname)
    # Create a new user
    new_user = User(
        username=username,
        email=user.email,
        date_of_birth=user.date_of_birth,
        name=user.name,
        gender = user.gender,
        surname=user.surname,
        status = "pending",
        phone_number=user.phone_number if user.phone_number else None,
        role="customer"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# add image to user profile
@user_router.post("/image/{user_id}")
async def add_profile_image(user_id:UUID,file: UploadFile = File(...), db:Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 1. Read the file contents
    contents = await file.read()       # bytes
    
    # 2. check if user profile alread exists if so then update
    if user.profile_image:
        user.profile_image.image_data = contents

    else:
    # 3. Create the RequestImage row if it wasnt already created
        img = ProfileImage(
            user_id=user.id,
            image_data = contents
        )
    
        db.add(img)
        db.commit()
        db.refresh(img)
    
    db.commit()

    return {"msg": "successful", "image_id": img.id if user.profile_image is None else user.profile_image.id}

#get image of user profile
@user_router.get("/image/{user_id}")
def get_profile_image(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.profile_image:
        raise HTTPException(status_code=404, detail="Profile image not found")
    
    return StreamingResponse(BytesIO(user.profile_image.image_data), media_type="image/png")
   


# Endpoint to get user details by username
@user_router.get("/{username}", response_model=List[UserBase])
def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).all()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

#endpoint to get user details by id
@user_router.get("/{user_id}/user",response_model=UserBase)
def get_user_by_id(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Endpoint to update user details
@user_router.put("/{email}", response_model=UserBase)
def update_user(email: str, user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == email).first()
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user details
    existing_user.email = user.email
    existing_user.name = user.name
    existing_user.surname = user.surname
    existing_user.date_of_birth = user.date_of_birth

    
    db.commit()
    db.refresh(existing_user)
    return existing_user

# Endpoint to delete a user
@user_router.delete("/{user_id}", response_model=UserBase)
def delete_user(user_id:UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"msg": "successful"}


# endpoint to get all users
@user_router.get("/", response_model=list[UserBase])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

# endpoint to check if a user exists by email
@user_router.get("/exists/{email}", response_model=bool)
def user_exists(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        return False
    else:
        return True