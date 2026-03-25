from __future__ import annotations

import asyncio

import aio_pika
from aio_pika.abc import AbstractQueue, AbstractRobustChannel, AbstractRobustConnection


class RabbitBroker:
    def __init__(
        self,
        *,
        amqp_url: str,
        queue_name: str,
        prefetch_count: int = 1,
        connect_timeout_sec: float = 10.0,
    ) -> None:
        self.amqp_url = amqp_url.strip()
        self.queue_name = queue_name.strip()
        self.prefetch_count = max(int(prefetch_count), 1)
        self.connect_timeout_sec = float(connect_timeout_sec)

        self._connection: AbstractRobustConnection | None = None
        self._channel: AbstractRobustChannel | None = None
        self._queue: AbstractQueue | None = None
        self._lock = asyncio.Lock()

    async def ensure_ready(self) -> None:
        await self._ensure_queue()

    async def publish_job(self, job_id: str) -> None:
        value = str(job_id).strip()
        if not value:
            raise ValueError("job_id is required")

        queue = await self._ensure_queue()
        if self._channel is None:
            raise RuntimeError("RabbitMQ channel is not initialized")

        message = aio_pika.Message(
            body=value.encode("utf-8"),
            content_type="text/plain",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await self._channel.default_exchange.publish(message, routing_key=queue.name)

    async def consume_job(self, timeout_sec: float | None = None) -> str | None:
        queue = await self._ensure_queue()

        try:
            if timeout_sec is None:
                message = await queue.get(fail=False)
            else:
                message = await queue.get(fail=False, timeout=timeout_sec)
        except asyncio.TimeoutError:
            return None

        if message is None:
            return None

        async with message.process(requeue=False):
            payload = message.body.decode("utf-8", errors="replace").strip()
            if not payload:
                return None
            return payload

    async def close(self) -> None:
        async with self._lock:
            if self._channel is not None and not self._channel.is_closed:
                await self._channel.close()
            self._channel = None
            self._queue = None

            if self._connection is not None and not self._connection.is_closed:
                await self._connection.close()
            self._connection = None

    async def _ensure_queue(self) -> AbstractQueue:
        if self._queue is not None and self._channel is not None and not self._channel.is_closed:
            return self._queue

        async with self._lock:
            if self._queue is not None and self._channel is not None and not self._channel.is_closed:
                return self._queue

            if self._connection is None or self._connection.is_closed:
                self._connection = await aio_pika.connect_robust(
                    self.amqp_url,
                    timeout=self.connect_timeout_sec,
                )

            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=self.prefetch_count)
            self._queue = await self._channel.declare_queue(self.queue_name, durable=True)
            return self._queue

