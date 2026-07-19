import os
from fastapi import FastAPI
from config import settings
from contextlib import asynccontextmanager as acm
from models.opensearch_manager import OpenSearchManager

# Load variables from .env file into os.environ
#load_dotenv()


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

# TODO: Finish these APIs
@app.get("/users")
def fetch_users(email:str="", limit:int = 100, offset:int = 10):
    return {}

@app.put("/users/update")
def update_users(email:str, payload:dict):
    return {}

@app.post("/users/create")
def create_user(payload:dict):
    return {}

@app.delete("/users/delete")
def delete_user(email:str):
    return {}

@app.get("/graphql")
def graphql_endpoint():
    return {}
