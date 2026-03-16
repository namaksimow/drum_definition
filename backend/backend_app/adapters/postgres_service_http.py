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

    async def list_public_courses(self, *, query: str | None, limit: int, offset: int) -> tuple[int, dict | str]:
        params = {"limit": str(limit), "offset": str(offset)}
        if query:
            params["q"] = query
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.get(f"{self.base_url}/community/courses", params=params)
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service courses list request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def create_course(
        self,
        *,
        token: str,
        title: str,
        description: str | None = None,
        visibility: str | None = None,
        tags: list[str] | None = None,
        cover_image_path: str | None = None,
    ) -> tuple[int, dict | str]:
        request_payload: dict[str, object] = {"title": title}
        if description is not None:
            request_payload["description"] = description
        if visibility is not None:
            request_payload["visibility"] = visibility
        if tags is not None:
            request_payload["tags"] = tags
        if cover_image_path is not None:
            request_payload["cover_image_path"] = cover_image_path
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.post(
                    f"{self.base_url}/me/courses",
                    json=request_payload,
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service create course request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def list_personal_courses(
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
                    f"{self.base_url}/me/courses",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service personal courses list request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def update_personal_course(
        self,
        *,
        token: str,
        course_id: int,
        title: str | None = None,
        description: str | None = None,
        visibility: str | None = None,
        tags: list[str] | None = None,
        cover_image_path: str | None = None,
    ) -> tuple[int, dict | str]:
        patch_payload: dict[str, object] = {}
        if title is not None:
            patch_payload["title"] = title
        if description is not None:
            patch_payload["description"] = description
        if visibility is not None:
            patch_payload["visibility"] = visibility
        if tags is not None:
            patch_payload["tags"] = tags
        if cover_image_path is not None:
            patch_payload["cover_image_path"] = cover_image_path
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.patch(
                    f"{self.base_url}/me/courses/{course_id}",
                    json=patch_payload,
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service personal course update request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def delete_personal_course(self, *, token: str, course_id: int) -> tuple[int, dict | str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.delete(
                    f"{self.base_url}/me/courses/{course_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service personal course delete request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def list_public_course_lessons(self, *, course_id: int) -> tuple[int, dict | str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.get(f"{self.base_url}/community/courses/{course_id}/lessons")
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service public lessons list request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def list_personal_course_lessons(self, *, token: str, course_id: int) -> tuple[int, dict | str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.get(
                    f"{self.base_url}/me/courses/{course_id}/lessons",
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service personal lessons list request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def create_personal_course_lesson(
        self,
        *,
        token: str,
        course_id: int,
        title: str,
        content: str | None = None,
        position: int | None = None,
    ) -> tuple[int, dict | str]:
        body: dict[str, object] = {"title": title}
        if content is not None:
            body["content"] = content
        if position is not None:
            body["position"] = int(position)
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.post(
                    f"{self.base_url}/me/courses/{course_id}/lessons",
                    json=body,
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service personal lesson create request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def update_personal_course_lesson(
        self,
        *,
        token: str,
        course_id: int,
        lesson_id: int,
        title: str | None = None,
        content: str | None = None,
        position: int | None = None,
    ) -> tuple[int, dict | str]:
        body: dict[str, object] = {}
        if title is not None:
            body["title"] = title
        if content is not None:
            body["content"] = content
        if position is not None:
            body["position"] = int(position)
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.patch(
                    f"{self.base_url}/me/courses/{course_id}/lessons/{lesson_id}",
                    json=body,
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service personal lesson update request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def delete_personal_course_lesson(
        self,
        *,
        token: str,
        course_id: int,
        lesson_id: int,
    ) -> tuple[int, dict | str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.delete(
                    f"{self.base_url}/me/courses/{course_id}/lessons/{lesson_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service personal lesson delete request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def list_personal_course_lesson_progress(self, *, token: str, course_id: int) -> tuple[int, dict | str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.get(
                    f"{self.base_url}/me/courses/{course_id}/lessons/progress",
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service lesson progress list request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def set_personal_course_lesson_progress(
        self,
        *,
        token: str,
        course_id: int,
        lesson_id: int,
        completed: bool,
    ) -> tuple[int, dict | str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.patch(
                    f"{self.base_url}/me/courses/{course_id}/lessons/{lesson_id}/progress",
                    json={"completed": bool(completed)},
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service lesson progress update request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def track_personal_course_visit(
        self,
        *,
        token: str,
        course_id: int,
    ) -> tuple[int, dict | str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.post(
                    f"{self.base_url}/me/courses/{course_id}/visit",
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service course visit tracking request failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def get_personal_course_statistics(
        self,
        *,
        token: str,
        course_id: int,
    ) -> tuple[int, dict | str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.get(
                    f"{self.base_url}/me/courses/{course_id}/stats",
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service course stats request failed: {exc}") from exc

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

    async def get_personal_author_role_request(self, *, token: str) -> tuple[int, dict | str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.get(
                    f"{self.base_url}/me/author-role-request",
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service author-role request get failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def create_personal_author_role_request(
        self,
        *,
        token: str,
        message: str,
    ) -> tuple[int, dict | str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.post(
                    f"{self.base_url}/me/author-role-request",
                    json={"message": message},
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service author-role request create failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def list_admin_author_role_requests(
        self,
        *,
        token: str,
        status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[int, dict | str]:
        params = {"limit": str(limit), "offset": str(offset)}
        if status is not None and status.strip():
            params["status"] = status.strip()
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.get(
                    f"{self.base_url}/admin/author-role-requests",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service admin author-role list failed: {exc}") from exc

        try:
            payload: dict | str = resp.json()
        except ValueError:
            payload = resp.text
        return resp.status_code, payload

    async def update_admin_author_role_request(
        self,
        *,
        token: str,
        request_id: int,
        status: str,
        admin_message: str | None = None,
    ) -> tuple[int, dict | str]:
        body: dict[str, str] = {"status": status}
        if admin_message is not None:
            body["admin_message"] = admin_message
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.patch(
                    f"{self.base_url}/admin/author-role-requests/{request_id}",
                    json=body,
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"PostgreSQL service admin author-role update failed: {exc}") from exc

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
