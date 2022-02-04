import asyncio
import contextlib
import contextvars
import logging
from aio_pika import Message

lg = logging.getLogger("mmf")
lg.setLevel(level=logging.DEBUG)
current_task_id = contextvars.ContextVar("current_task_id", default=None)


@contextlib.contextmanager
def set_task_id(task_id):
    token = current_task_id.set(task_id)
    try:
        yield
    finally:
        current_task_id.reset(token)


class AsyncQueueHandler(logging.Handler):
    def __init__(self, *args, queue: asyncio.Queue, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = queue

    def emit(self, record: logging.LogRecord) -> None:
        task_id = current_task_id.get()
        setattr(record, "taskid", task_id)
        self.queue.put_nowait(record)


@contextlib.contextmanager
def add_rabbit_handler(loop: asyncio.AbstractEventLoop, lg: logging.Logger):
    q = asyncio.Queue()
    hndlr = AsyncQueueHandler(queue=q)
    lg.addHandler(hndlr)

    async def run():
        from .rabbit_wrapper import get_exchange

        ex, *_ = await get_exchange()
        try:
            while True:
                record: logging.LogRecord = await q.get()
                msg = hndlr.format(record)
                headers = {"type": "log", "level": record.levelname}
                task_id = getattr(record, "taskid", None)
                if task_id:
                    headers["task-id"] = task_id
                await asyncio.shield(
                    ex.publish(
                        message=Message(
                            body=msg.encode(),
                            headers=headers,
                        ),
                        routing_key="",
                    )
                )

        except asyncio.CancelledError:
            return

    task = loop.create_task(run())
    try:
        yield
    finally:
        lg.removeHandler(hndlr)
        task.cancel()
        loop.run_until_complete(task)
