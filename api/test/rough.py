import os
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, HttpUrl
import aiohttp

# --- CONFIGURATION ---
OPENSEARCH_BASE = "https://localhost:9200"
INDEX_NAME = "users"
ADMIN_PASSWORD = os.getenv("OPENSEARCH_PASSWORD", "mySecurePassword123!")
# Basic Auth header config
AUTH = aiohttp.BasicAuth("admin", ADMIN_PASSWORD)

# --- PYDANTIC SCHEMAS ---
class UserMetadata(BaseModel):
    phone: List[str]
    url: HttpUrl

class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    metadata: UserMetadata

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    metadata: Optional[UserMetadata] = None

# --- HTTP LIFESPAN CLIENT ---
http_session: Optional[aiohttp.ClientSession] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_session
    # Disable SSL verification for local self-signed testing certificates
    connector = aiohttp.TCPConnector(ssl=False)
    http_session = aiohttp.ClientSession(connector=connector, auth=AUTH)
    
    # Check/Create Index manually via PUT request
    async with http_session.get(f"{OPENSEARCH_BASE}/{INDEX_NAME}") as resp:
        if resp.status == 404:
            await http_session.put(f"{OPENSEARCH_BASE}/{INDEX_NAME}")
            
    yield
    await http_session.close()

app = FastAPI(lifespan=lifespan)

# --- CRUD ROUTING ---

@app.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    # Check if doc exists: HEAD https://localhost:9200/users/_doc/email
    async with http_session.head(f"{OPENSEARCH_BASE}/{INDEX_NAME}/_doc/{user.email}") as resp:
        if resp.status == 200:
            raise HTTPException(status_code=400, detail="User already exists.")
            
    # Write doc: PUT https://localhost:9200/users/_doc/email?refresh=true
    payload = user.model_dump(mode="json")
    url = f"{OPENSEARCH_BASE}/{INDEX_NAME}/_doc/{user.email}?refresh=true"
    
    async with http_session.put(url, json=payload) as resp:
        if resp.status not in [200, 201]:
            raise HTTPException(status_code=500, detail="Failed to write to cluster")
    return {"message": "User created successfully", "email": user.email}


@app.get("/users/{email}", response_model=UserCreate)
async def get_user(email: EmailStr):
    url = f"{OPENSEARCH_BASE}/{INDEX_NAME}/_doc/{email}"
    async with http_session.get(url) as resp:
        if resp.status == 404:
            raise HTTPException(status_code=404, detail="User not found.")
        data = await resp.json()
        return data["_source"]


@app.put("/users/{email}")
async def update_user(email: EmailStr, user_update: UserUpdate):
    update_data = user_update.model_dump(exclude_none=True, mode="json")
    if not update_data:
        raise HTTPException(status_code=400, detail="No parameters provided.")
        
    # OpenSearch update API format calls the _update route with a "doc" object
    url = f"{OPENSEARCH_BASE}/{INDEX_NAME}/_update/{email}?refresh=true"
    payload = {"doc": update_data}
    
    async with http_session.post(url, json=payload) as resp:
        if resp.status == 404:
            raise HTTPException(status_code=404, detail="User not found.")
    return {"message": "User updated successfully", "email": email}


@app.delete("/users/{email}")
async def delete_user(email: EmailStr):
    url = f"{OPENSEARCH_BASE}/{INDEX_NAME}/_doc/{email}?refresh=true"
    async with http_session.delete(url) as resp:
        if resp.status == 404:
            raise HTTPException(status_code=404, detail="User not found.")
    return {"message": "User deleted successfully", "email": email}
