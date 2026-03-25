from __future__ import annotations

import asyncio

from ml_service.bootstrap import get_container


async def _run() -> None:
    container = get_container()
    stop_event = asyncio.Event()
    print("ML worker is running. Press Ctrl+C to stop.")
    try:
        await container.job_service.run_worker_loop(
            stop_event=stop_event,
            poll_timeout_sec=container.settings.worker_poll_timeout_sec,
        )
    finally:
        close_queue = getattr(container.job_queue, "close", None)
        if callable(close_queue):
            await close_queue()


def main() -> None:
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
