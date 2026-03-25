from __future__ import annotations

import httpx

from ml_service.ports.queue import JobQueue


class QueueServiceHttpAdapter(JobQueue):
    def __init__(self, *, base_url: str, timeout_sec: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = float(timeout_sec)

    async def publish(self, job_id: str) -> None:
        value = str(job_id).strip()
        if not value:
            raise ValueError("job_id is required")

        last_resp: httpx.Response | None = None
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                for path in self._publish_paths():
                    resp = await client.post(f"{self.base_url}{path}", json={"job_id": value})
                    last_resp = resp
                    if resp.status_code == 200:
                        return
                    if resp.status_code != 404:
                        raise RuntimeError(
                            f"Queue publish failed [{resp.status_code}] {self.base_url}{path}: {resp.text}"
                        )
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Queue publish failed: {exc}") from exc

        if last_resp is None:
            raise RuntimeError("Queue publish failed: no response from queue service")
        raise RuntimeError(
            "Queue publish failed: queue endpoint not found. "
            f"Checked {self.base_url}/v1/jobs and {self.base_url}/api/v1/jobs. "
            f"Last response [{last_resp.status_code}]: {last_resp.text}"
        )

    async def consume(self, timeout: float | None = None) -> str | None:
        timeout_sec = 30.0 if timeout is None else max(float(timeout), 0.0)
        last_resp: httpx.Response | None = None
        try:
            async with httpx.AsyncClient(timeout=max(self.timeout_sec, timeout_sec + 1.0)) as client:
                for path in self._consume_paths():
                    resp = await client.get(
                        f"{self.base_url}{path}",
                        params={"timeout_sec": timeout_sec},
                    )
                    last_resp = resp
                    if resp.status_code == 200:
                        payload = resp.json()
                        break
                    if resp.status_code != 404:
                        raise RuntimeError(
                            f"Queue consume failed [{resp.status_code}] {self.base_url}{path}: {resp.text}"
                        )
                else:
                    raise RuntimeError(
                        "Queue consume failed: queue endpoint not found. "
                        f"Checked {self.base_url}/v1/jobs/consume and {self.base_url}/api/v1/jobs/consume. "
                        f"Last response [{last_resp.status_code if last_resp else 'n/a'}]: "
                        f"{last_resp.text if last_resp else 'no response'}"
                    )
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Queue consume failed: {exc}") from exc

        if not isinstance(payload, dict):
            return None

        job_id = payload.get("job_id")
        if job_id is None:
            return None

        value = str(job_id).strip()
        return value or None

    def _publish_paths(self) -> tuple[str, ...]:
        if self.base_url.endswith("/api"):
            return ("/v1/jobs",)
        return ("/v1/jobs", "/api/v1/jobs")

    def _consume_paths(self) -> tuple[str, ...]:
        if self.base_url.endswith("/api"):
            return ("/v1/jobs/consume",)
        return ("/v1/jobs/consume", "/api/v1/jobs/consume")
