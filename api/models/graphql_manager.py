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
    async def user(self, email: str) -> User | None:
        url = f"{settings.OPENSEARCH_URL}/users/_doc/{email}"
        async with http_session.get(url) as resp:
            if resp.status != 200:
                return None
            src = (await resp.json())["_source"]
            return User(email=email, first_name=src["first_name"], last_name=src["last_name"])


schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)