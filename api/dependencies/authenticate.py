from typing import Annotated
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from jwt.exceptions import InvalidTokenError

import jwt
import os

from fastapi import Depends, HTTPException, status
from typing_extensions import Annotated
from ..app import db
from ..users.user_models import User

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES")
users_collection = db.get_collection(os.environ.get("USER_COLLECTION"))

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=1440)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

from ..users.user_routes import oauth2_scheme
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = await users_collection.find_one({'email': email})
    if user is None:
        raise credentials_exception
    del user['_id']
    del user['password']
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return User(**current_user)
