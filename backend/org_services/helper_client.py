import httpx
import logging

logger = logging.getLogger(__name__)


class HelperClient:
    def __init__(self):
        from org_config import get_settings
        settings = get_settings()
        self.base_url = settings.BIPTHELPER_URL.rstrip("/")
        self.api_key = settings.ORGANIZER_API_KEY
        self._client = httpx.Client(timeout=30)

    def _headers(self):
        return {"X-Organizer-Key": self.api_key}

    def ingest_document(self, doc_data: dict):
        resp = self._client.post(
            f"{self.base_url}/api/documents",
            json=doc_data,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def update_document(self, doc_id: str, data: dict):
        resp = self._client.put(
            f"{self.base_url}/api/documents/{doc_id}",
            json=data,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def delete_document(self, doc_id: str):
        resp = self._client.delete(
            f"{self.base_url}/api/documents/{doc_id}",
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def get_categories(self):
        resp = self._client.get(
            f"{self.base_url}/api/documents/categories",
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def get_documents(self, params: dict):
        resp = self._client.get(
            f"{self.base_url}/api/documents",
            params=params,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def approve_document(self, doc_id: str, categories: str = None):
        payload = {}
        if categories:
            payload["categories"] = categories
        resp = self._client.post(
            f"{self.base_url}/api/documents/{doc_id}/approve",
            json=payload,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return resp.json()