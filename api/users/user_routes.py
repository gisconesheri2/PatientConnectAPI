from typing import Annotated

from fastapi import status, Body, HTTPException, Depends, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import os
import bcrypt

from ..app import db
from .user_models import UserRegistration
from .token_models import Token
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))



salt = bcrypt.gensalt()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/users/login')
router = APIRouter()
users_collection = db.get_collection(os.environ.get("USER_COLLECTION"))
facilities_collection = db.get_collection(os.environ.get('FACILITIES_COLLECTION'))

from ..dependencies.authenticate import create_access_token, get_current_active_user

@router.post('/users/register',
        summary="Register a new user(healthcare facility)",
        response_description="New user created",
        status_code=status.HTTP_201_CREATED,
        response_model_by_alias=False,
        )
async def register_user(user: UserRegistration = Body(...)):
    """Register a user to the service.
        User is defined as a registered healthcare facility.
        The data for registration must be provided in JSON format
        and should include the following fields:

        {
            email: "STRING" official email of the healthcare facility (must be unique)
            password: "STRING" An alphanumeric string
            facility_name: "STRING" Facility name as registered by relevant regulatory body (PPB for now)(must be unique)
        }
        The facility has to be confirmed as registered before accessing patient information

    Returns:

        (JSON) Status of user created if user is saved successfully in the database.
        (JSON) Status of Error encountered in parsing data in form of:
                field with a problem: reason parsing fails
    """
    # raw_data = request.get_json()
    # validate the json data received against the model
    data = user.model_dump(by_alias=True, exclude=['id'])
    #if email is already registered, return an error
    if await users_collection.find_one({'email': data['email']}):
        raise HTTPException(status_code=400, detail='Email/User exists')
    
    #if facility is already registered, return an error
    if await users_collection.find_one({'facility_name': data['facility_name']}):
        raise HTTPException(status_code=400, detail='Facility already registered')
    
    # check if facility is duly registered
    facility = await facilities_collection.find_one({'facility_name': data['facility_name']})
    if not facility:
        raise HTTPException(status_code=400, detail='Facility is not registered to offer services')
    if facility['status'] != 'Active':
        raise HTTPException(status_code=400, detail='Facility license is revoked')
    
    #save the user to the database
    hash_pd = bcrypt.hashpw(data['password'].encode('utf-8'), salt)
    data['password'] = hash_pd.decode('utf-8')
    data['facility_type'] = facility['facility_type']
    user = await users_collection.insert_one(data)
    print('new user created')
    return {'status': 'user_created'}
    

@router.post('/users/login', response_model=Token,
    summary="Log in user and generate access token")
async def login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Login a user to the service.
        user is defined as a registered healthcare facility.
        The data for login is provided via an OAuth form with these fields.

        username: email of the healthcare facility used in registration
        password: An alphanumeric string
        
    Returns:
    
        (JSON) An Access token if user is logged in successfully.
        (JSON) Status of Error encountered 
    """
    # get the form data received from OAuth
    data = {'email': form_data.username, 'password': form_data.password}

    #if email is already registered, check password and generate access token, else return error
    user = await users_collection.find_one({'email': data['email']})
    if not user:
        raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email",
        headers={"WWW-Authenticate": "Bearer"},
        )
    
    fm_pwd_bytes = form_data.password.encode('utf-8')
    ur_pwd_bytes = user['password'].encode('utf-8')
    if not bcrypt.checkpw(fm_pwd_bytes, ur_pwd_bytes):
        raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    access_token = create_access_token(data={'sub': user['email']})
    print('user logged in')
    return Token(access_token=access_token, token_type="bearer")                       
