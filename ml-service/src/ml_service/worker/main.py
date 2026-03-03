from __future__ import annotations

import asyncio

from ml_service.bootstrap import get_container


async def _run() -> None:
    container = get_container()
    stop_event = asyncio.Event()
    print("Mock worker is running. Press Ctrl+C to stop.")
    await container.job_service.run_worker_loop(
        stop_event=stop_event,
        poll_timeout_sec=container.settings.worker_poll_timeout_sec,
    )


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()

