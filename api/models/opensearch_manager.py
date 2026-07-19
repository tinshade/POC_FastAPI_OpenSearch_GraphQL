import logging
from typing import List, Optional
from contextlib import asynccontextmanager as acm
from opensearchpy import AsyncOpenSearch
from fastapi import FastAPI
from config import settings



# Set up logging for tracking cluster setup errors
logger = logging.getLogger(__name__)


class OpenSearchManager:
    def __init__(self):
        self.opensearch_client: Optional[AsyncOpenSearch] = None

    def get_opensearch_client_instance(self) -> AsyncOpenSearch:
        if self.opensearch_client:
            return self.opensearch_client
        self.opensearch_client = AsyncOpenSearch(
            hosts = [settings.OPENSEARCH_URL],
            http_auth = ("admin", settings.OPENSEARCH_ADMIN_PASSWORD),
            use_ssl = True,
            verify_certs = settings.IS_PROD,
            ssl_show_warn=False
        )
        
        return self.opensearch_client

    async def initialize_opensearch_indices(self, indices:List[str]):
        
        client = self.get_opensearch_client_instance()
        for index in indices:
            if not await client.indices.exists(index=index):
                await client.indices.create(index=index)

    async def gracefully_shutdown_opensearch(self):
        # Safely close connection pool on shutdown
        await self.opensearch_client.close()

    @acm
    async def opensearch_lifespan(self, app:FastAPI, indices:List[str]):
        try:
            self.get_opensearch_client_instance()
            await self.initialize_opensearch_indices(indices)
            logger.info("Opensearch client initialized and verified successfully!")
            
            yield

        except Exception as e:
            logger.error(f"Error while initializing Opensearch: {e}")
            raise e
        
        finally:
            logger.info("Shutting down OpenSearch connections...")
            await self.gracefully_shutdown_opensearch()



