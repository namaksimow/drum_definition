from __future__ import annotations

import httpx

from backend_app.application.ports.postgres_service_port import PostgresServicePort
from backend_app.domain.errors import ExternalServiceError


class PostgresServiceHttpAdapter(PostgresServicePort):
    def __init__(self, base_url: str, timeout_sec: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec

    async def list_public_tablatures(self, *, query: str | None, limit: int, offset: int) -> tuple[int, dict | str]:
        params = {"limit": str(limit), "offset": str(offset)}
        if query:
            params["q"] = query
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.get(f"{self.base_url}/community/tablatures", params=params)
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service list request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def get_public_tablature(self, *, tablature_id: int) -> tuple[int, dict | str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.get(f"{self.base_url}/community/tablatures/{tablature_id}")
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service get request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def list_public_tablature_comments(
        self,
        *,
        tablature_id: int,
        limit: int,
        offset: int,
    ) -> tuple[int, dict | str]:
        params = {"limit": str(limit), "offset": str(offset)}
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.get(
                    f"{self.base_url}/community/tablatures/{tablature_id}/comments",
                    params=params,
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service comments list request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def create_public_tablature_comment(
        self,
        *,
        token: str,
        tablature_id: int,
        content: str,
    ) -> tuple[int, dict | str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.post(
                    f"{self.base_url}/community/tablatures/{tablature_id}/comments",
                    json={"content": content},
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service comment create request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def get_public_tablature_reactions(
        self,
        *,
        tablature_id: int,
        token: str | None = None,
    ) -> tuple[int, dict | str]:
        headers = {"Authorization": f"Bearer {token}"} if token else None
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.get(
                    f"{self.base_url}/community/tablatures/{tablature_id}/reactions",
                    headers=headers,
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service reactions get request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def set_public_tablature_reaction(
        self,
        *,
        token: str,
        tablature_id: int,
        reaction_type: str,
    ) -> tuple[int, dict | str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.post(
                    f"{self.base_url}/community/tablatures/{tablature_id}/reactions",
                    json={"reaction_type": reaction_type},
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service reactions set request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def register_user(self, *, email: str, password: str, nickname: str) -> tuple[int, dict | str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.post(
                    f"{self.base_url}/auth/register",
                    json={
                        "email": email,
                        "password": password,
                        "nickname": nickname,
                    },
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service register request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def login_user(self, *, email: str, password: str) -> tuple[int, dict | str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.post(
                    f"{self.base_url}/auth/login",
                    json={
                        "email": email,
                        "password": password,
                    },
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service login request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def get_current_user(self, *, token: str) -> tuple[int, dict | str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.get(
                    f"{self.base_url}/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service me request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def update_current_user(self, *, token: str, nickname: str) -> tuple[int, dict | str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.patch(
                    f"{self.base_url}/auth/me",
                    json={"nickname": nickname},
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service update-me request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def list_personal_tablatures(
        self,
        *,
        token: str,
        query: str | None,
        limit: int,
        offset: int,
    ) -> tuple[int, dict | str]:
        params = {"limit": str(limit), "offset": str(offset)}
        if query:
            params["q"] = query
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.get(
                    f"{self.base_url}/me/tablatures",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service personal list request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def get_personal_tablature(self, *, token: str, tablature_id: int) -> tuple[int, dict | str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.get(
                    f"{self.base_url}/me/tablatures/{tablature_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service personal get request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def update_personal_tablature(
        self,
        *,
        token: str,
        tablature_id: int,
        track_file_name: str | None = None,
        visibility: str | None = None,
        json_format: dict | None = None,
    ) -> tuple[int, dict | str]:
        patch_payload: dict[str, object] = {}
        if track_file_name is not None:
            patch_payload["track_file_name"] = track_file_name
        if visibility is not None:
            patch_payload["visibility"] = visibility
        if json_format is not None:
            patch_payload["json_format"] = json_format
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.patch(
                    f"{self.base_url}/me/tablatures/{tablature_id}",
                    json=patch_payload,
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service personal update request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload
