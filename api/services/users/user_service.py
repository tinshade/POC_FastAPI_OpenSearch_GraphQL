from fastapi import HTTPException
from config import settings

class UserService:
    def __init__(self, session):
        self.session = session

    async def get_user(self, email):
        url = f"{settings.OPENSEARCH_URL}/users/_doc/{email}"

        async with self.session.get(url) as resp:
            if resp.status == 404:
                return None

            if resp.status != 200:
                raise HTTPException(resp.status)

            return (await resp.json())["_source"]

    async def get_users(self, limit=100, offset=0):
        url = (
            f"{settings.OPENSEARCH_URL}/users/_search"
            f"?size={limit}&from={offset}"
        )

        async with self.session.get(url) as resp:
            if resp.status != 200:
                raise HTTPException(resp.status)

            data = await resp.json()

        return [hit["_source"] for hit in data["hits"]["hits"]]

    async def create_user(self, user):
        ...