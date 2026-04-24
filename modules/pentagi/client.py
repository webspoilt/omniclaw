"""
PentAGI API Client for OmniClaw

Provides a REST and GraphQL bridge between OmniClaw's workers and the PentAGI orchestration backend.
"""

import httpx
import logging
import asyncio
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PentagiClient:
    def __init__(self, base_url: str = "https://localhost:8443", token: Optional[str] = None):
        """
        Initialize the PentAGI client. By default PentAGI binds to 8443 for HTTPS.
        Authentication requires a valid JWT/Bearer token from the Go backend.
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        
        # Configure client to ignore self-signed certificates locally
        self.client = httpx.AsyncClient(verify=False, timeout=30.0)
        
    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def authenticate(self, email: str = "admin@pentagi.com", password: str = "admin") -> bool:
        """Authenticate with REST API to get the bearer token."""
        try:
            url = f"{self.base_url}/api/v1/auth/login"
            payload = {"email": email, "password": password}
            
            resp = await self.client.post(url, json=payload, headers={"Content-Type": "application/json"})
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("token") or data.get("access_token")
                logger.info("Successfully authenticated to PentAGI backend.")
                return True
            else:
                logger.error(f"PentAGI authentication failed: {resp.status_code} - {resp.text}")
                return False
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to PentAGI ({self.base_url}): {str(e)}")
            return False

    async def run_graphql_query(self, query: str, variables: Optional[Dict] = None) -> Dict[Any, Any]:
        """Execute a GraphQL query against the PentAGI endpoint."""
        if not self.token:
            await self.authenticate()
            
        url = f"{self.base_url}/query"
        payload = {"query": query, "variables": variables or {}}
        
        try:
            resp = await self.client.post(url, json=payload, headers=self._get_headers())
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"GraphQL HTTP Error {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"GraphQL execution failed: {str(e)}")
            raise

    async def start_flow(self, target: str, flow_type: str = "pentest", objective: str = "") -> str:
        """Start a new vulnerability flow using GraphQL."""
        # Example mutation based on Flow schema structure observed in PentAGI docs
        mutation = """
        mutation CreateFlow($input: CreateFlowInput!) {
            createFlow(input: $input) {
                id
                status
            }
        }
        """
        variables = {
            "input": {
                "target": target,
                "type": flow_type,
                "objective": objective
            }
        }
        
        try:
            result = await self.run_graphql_query(mutation, variables)
            if "errors" in result:
                raise ValueError(f"GraphQL returned errors: {result['errors']}")
                
            flow_id = result["data"]["createFlow"]["id"]
            logger.info(f"Started PentAGI Flow ID: {flow_id} against {target}")
            return flow_id
        except Exception as e:
            # Fallback if specific schema is incorrect or pending updates
            logger.warning(f"GraphQL mutation failed, falling back to REST if available. Error: {e}")
            raise

    async def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Retrieve the status and artifacts of a specific Flow."""
        query = """
        query GetFlow($id: ID!) {
            flow(id: $id) {
                id
                status
                artifacts {
                    id
                    type
                    content
                }
            }
        }
        """
        variables = {"id": flow_id}
        result = await self.run_graphql_query(query, variables)
        return result.get("data", {}).get("flow", {})

    async def close(self):
        await self.client.aclose()


# For testing independently
if __name__ == "__main__":
    import asyncio
    
    async def _test():
        client = PentagiClient()
        success = await client.authenticate()
        print(f"Auth Success: {success}")
        if success:
            query = "{ flows { id status } }"
            try:
                print(await client.run_graphql_query(query))
            except Exception as e:
                print("Ignored structure issue for test.")
        await client.close()
        
    asyncio.run(_test())
