import os
from fastapi import FastAPI, HTTPException
from config import settings
from contextlib import asynccontextmanager as acm
from models.opensearch_manager import OpenSearchManager
from pydantic import EmailStr
from typing import Optional
from models.users.user import UserCreate, UserUpdate
import aiohttp
from services.users.user_service import UserService

# Initialize Opensearch Instance
opensearch_manager = OpenSearchManager()
http_session:aiohttp.ClientSession = None


@acm
async def app_lifespan(app: FastAPI):
    # Pass control down to your custom manager
    global http_session
    connector = aiohttp.TCPConnector(ssl=False)
    http_session = aiohttp.ClientSession(connector=connector, auth=aiohttp.BasicAuth("admin", settings.OPENSEARCH_ADMIN_PASSWORD))

    try:
        # Check/Create Index manually via PUT request
        async with http_session.get(f"{settings.OPENSEARCH_URL}/users") as resp:
            if resp.status == 404:
                await http_session.put(f"{settings.OPENSEARCH_URL}/users")
        
        async with opensearch_manager.opensearch_lifespan(app, settings.INDICES):
            yield
    finally:
        await http_session.close()
        
# Initialize the server instance
app = FastAPI(lifespan=app_lifespan)
user_service = UserService(http_session)

import strawberry
from strawberry.fastapi import GraphQLRouter
from typing import List, Optional


@strawberry.type
class UserMetadata:
    phone: Optional[List[str]]
    url: str

@strawberry.type
class User:
    email: str
    first_name: str
    last_name: str
    metadata: Optional[UserMetadata]


@strawberry.type
class Query:
    @strawberry.field
    async def user(email: str):
        result = await fetch_users(email=email)
        return User(**result["data"])


@strawberry.mutation
async def create_user(user: CreateUser):
    await create_user(
        UserCreate(**user.__dict__)
    )
    return True



schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)


@app.get("/")
@app.get("/health")
def health_check():
    print(settings.APP_NAME)
    return {"status": 200, "message": "healthy"}

@app.get("/users")
async def fetch_users(email: EmailStr = ""):
    if email:
        return await user_service.get_user(email)

    return await user_service.get_users()

@app.put("/users/update")
async def update_users(email: EmailStr, user_update: UserUpdate):
    update_data = user_update.model_dump(exclude_none=True, mode="json")
    if not update_data:
        raise HTTPException(status_code=400, detail="No parameters provided.")
        
    # OpenSearch update API format calls the _update route with a "doc" object
    url = f"{settings.OPENSEARCH_URL}/users/_update/{email}?refresh=true"
    payload = {"doc": update_data}
    
    async with http_session.post(url, json=payload) as resp:
        if resp.status != 200:
            raise HTTPException(status_code=resp.status, detail=resp.text)
    return {"message": "User updated successfully", "email": email}

@app.post("/users/create", status_code=201)
async def create_user(user: UserCreate):
    async with http_session.head(f"{settings.OPENSEARCH_URL}/users/_doc/{user.email}") as resp:
        print(resp.status, resp.text)
        if resp.status == 200:
            raise HTTPException(status_code=500, detail="User already exists!")
    
    payload = user.model_dump(mode="json")
    url = f"{settings.OPENSEARCH_URL}/users/_doc/{user.email}?refresh=true"
    async with http_session.put(url, json=payload) as resp:
        if resp.status not in (200, 201):
            raise HTTPException(status_code=resp.status, detail=f"Something went wrong while creating user with email {user.email}")

    return {"message": "User created successfully", "email": user.email}

@app.delete("/users/delete")
async def delete_user(email:EmailStr):
    url = f"{settings.OPENSEARCH_URL}/users/_doc/{email}?refresh=true"
    async with http_session.delete(url) as resp:
        if resp.status not in (200, 204):
            raise HTTPException(status_code=resp.status, detail=f"Something went wrong while deleting user with email {email}")
    return {}

app.include_router(graphql_app, prefix="/graphql")