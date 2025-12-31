import httpx
import os
from typing import List, Dict


class RetrievalClient:
    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = os.getenv(
            "RETRIEVAL_SERVICE_URL",
            "http://localhost:8001"
        ).rstrip("/")
        self.timeout = timeout

    def retrieve(
        self,
        query: str,
        top_k: int,
        jwt_token: str
    ) -> List[Dict]:
        """
        Call retrieval service and return retrieved chunks.
        """
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "query": query,
            "top_k": top_k
        }

        response = httpx.post(
            f"{self.base_url}/retrieve",
            json=payload,
            headers=headers,
            timeout=self.timeout
        )

        response.raise_for_status()

        data = response.json()
        return data["results"]
