from typing import List, Optional
from pydantic import BaseModel, EmailStr, HttpUrl

# Pydantic Schemas
class UserMetadata(BaseModel):
    phone:List[str]
    url:HttpUrl

class UserCreate(BaseModel):
    email:EmailStr
    first_name:str
    last_name:str
    metadata:UserMetadata

class UserUpdate(BaseModel):
    #email:EmailStr
    first_name:Optional[str] = None
    last_name:Optional[str] = None
    metadata:Optional[UserMetadata] = None

class UserDelete(BaseModel):
    email:EmailStr
