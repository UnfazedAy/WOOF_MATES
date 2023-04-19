"""
contains all routes solely related to the user
"""

from fastapi import Depends, APIRouter, File, Form, HTTPException, status
from fastapi_jwt_auth import AuthJWT
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import Annotated, List
from woofmate.schemas.createSchema import ICreateUser, IUser, LoginUser
from woofmate.functions.user_service import UserServices
from woofmate.database import get_db
from woofmate.functions.my_cloudinary import upload_image_to_cloudinary

auth_router = APIRouter(
    prefix='/auth',
    tags=["User Routes"]
)

UserServices = UserServices()


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user(
    profile_image: Annotated[bytes, File()],
    firstName: str = Form(...),
    lastName: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Sign up route to register user
    """
    if not profile_image:
        raise HTTPException(
            status_code=400, detail="Profile picture is required"
        )
    if not firstName:
        raise HTTPException(status_code=400, detail="First name is required")
    if not lastName:
        raise HTTPException(status_code=400, detail="Last name is required")
    if not password:
        raise HTTPException(status_code=400, detail="Password is required")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    if profile_image is None:
        raise HTTPException(
            status_code=400, detail="Profile picture is required"
        )

    # Limits the file upload to 1MB
    if len(profile_image) > 1000000:
        raise HTTPException(
            status_code=400,
            detail="Profile picture shouldn't be greater than 1MB"
        )

    # Uploads the image to cloudinary
    profile_image_url = await upload_image_to_cloudinary(
        'WOOF_MATES_USERS', profile_image, email, 'profile_image'
    )

    if not profile_image_url:
        raise HTTPException(status_code=500, detail="Failed to upload Image")

    # Creates the user with the image url
    user = await UserServices.createUser(
        db, firstName, lastName, email, password, profile_image_url
    )
    return user


@auth_router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    email: str = Form(...), password: str = Form(...),
    db: Session = Depends(get_db), Authorize: AuthJWT = Depends()
):
    """
    Validates the user credentials and returns the access token
    and refresh token
    """
    user_to_login = await UserServices.login(db, email, password)
    if user_to_login.email == email:
        access_token = Authorize.create_access_token(
            subject=user_to_login.email
        )
        refresh_token = Authorize.create_refresh_token(
            subject=user_to_login.email
        )
        response = {
            "access_token": f"Bearer {access_token}",
            "refresh_token": f"Bearer {refresh_token}"
        }

        return jsonable_encoder(response)


@auth_router.post('/forgotpassword', status_code=status.HTTP_200_OK)
async def forgotpassword(email: str,  db: Session = Depends(get_db)):
    """
    Implements the necessary validations and process
    to retrieve or reset a forgotten password
    """
    pass


@auth_router.get('/get_users',  response_model=List[IUser], status_code=200)
async def get_users(
    skip: int = 0, limit: int = 20, db: Session = Depends(get_db)
):
    """
    Get the users presents in the database and sets a default limit
    to the amount of users it displays at once (pagination)
    """
    users = UserServices.get_all_user(db, skip=skip, limit=limit)
    if len(users) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user(s) found"
        )
    return users


@auth_router.get(
    '/get_one_user/{user_id}',
    response_model=IUser, status_code=status.HTTP_200_OK
)
async def get_one_user(user_id: int, db: Session = Depends(get_db)):
    user = UserServices.get_one_user(db, id=user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user
