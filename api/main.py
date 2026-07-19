import os
from fastapi import FastAPI
from config import settings
from contextlib import asynccontextmanager as acm
from models.opensearch_manager import OpenSearchManager
from pydantic import EmailStr
from typing import Optional
from models.users.user import UserCreate, UserUpdate


# Initialize Opensearch Instance
opensearch_manager = OpenSearchManager()
@acm
async def app_lifespan(app: FastAPI):
    # Pass control down to your custom manager
    async with opensearch_manager.opensearch_lifespan(app, settings.INDICES):
        yield
        
# Initialize the server instance
app = FastAPI(lifespan=app_lifespan)

@app.get("/")
@app.get("/health")
def health_check():
    print(settings.APP_NAME)
    return {"status": 200, "message": "healthy"}

@app.get("/users")
async def fetch_users(email:EmailStr="", limit:int = 100, offset:int = 10):
    base_url:str = f"{settings.OPENSEARCH_URL}/users"
    url:str = f"{base_url}_doc/{email}" if email else f"{base_url}_search?size={limit}&from={offset}"
    data:dict = None
    async with http_session.get(url) as resp:
        if resp.status != 200:
            raise HTTPException(status_code=resp.status, detail="Error while getting user details")
        if email:
            data:dict = await resp.json()['_source']
        else:
            # Extracting the actual document sources from the search hits
            hits = res_data.get('hits', {}).get('hits', [])
            data = [hit['_source'] for hit in hits]
    return {"message": "User data retrieved successfully!", "data": data}

@app.put("/users/update")
async def update_users(email: EmailStr, user_update: UserUpdate):
    update_data = user_update.model_dump(exclude_none=True, mode="json")
    if not update_data:
        raise HTTPException(status_code=400, detail="No parameters provided.")
        
    # OpenSearch update API format calls the _update route with a "doc" object
    url = f"{OPENSEARCH_BASE}/users/_update/{email}?refresh=true"
    payload = {"doc": update_data}
    
    async with http_session.post(url, json=payload) as resp:
        if resp.status != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return {"message": "User updated successfully", "email": email}

@app.post("/users/create")
async def create_user(user: UserCreate):
    print(user, "debugging")
    return {}
    async with http_session.head(f"{settings.OPENSEARCH_URL}/users/_doc/{user.email}") as resp:
        if resp.status != 200:
            raise HTTPException(status_code=500, detail="Failed writing to cluster")

    return {"message": "User created successfully", "email": user.email}

@app.delete("/users/delete")
async def delete_user(email:EmailStr):
    url = f"{settings.OPENSEARCH_URL}/users/_doc/{email}?refresh=true"
    async with http_session.delete(url) as resp:
        if resp.status in (200, 204):
            raise HTTPException(status_code=resp.status, detail=f"Something went wrong while deleting user with email {email}")
    return {}

@app.get("/graphql")
def graphql_endpoint():
    return {}
