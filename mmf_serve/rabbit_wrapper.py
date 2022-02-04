import asyncio
import concurrent.futures
import inspect
import traceback
import typing
import urllib.parse
import orjson
from aio_pika import (
    connect_robust,
    RobustChannel,
    Exchange,
    IncomingMessage,
    Message,
    Channel,
    Queue,
    ExchangeType,
)
from mmf_meta.core import Target
from mmf_meta.descriptors import DescriptorBase, JsonFile, Dict
from requests import Session, Request
from mmf_serve.config import config
from .logger import lg, set_task_id

ex: Exchange = None
tasks_queue: Queue = None
ch_read: Channel = None
ch_write: Channel = None
_lck = asyncio.Lock()


async def get_exchange():
    global ex, tasks_queue, ch_write, ch_read
    if ex is not None:
        return ex, tasks_queue
    else:
        lg.info("connecting rabbitmq %s", config.rabbit.con_string)
        con = await connect_robust(config.rabbit.con_string)
        ch_read = await con.channel()
        ch_write = await con.channel()
        await ch_read.set_qos(prefetch_count=2)
        lg.info("get exchange %s", config.exchange_name)
        await asyncio.sleep(1)
        ex = await ch_write.get_exchange(
            config.exchange_name,
        )
        lg.info("get queue %s", config.queue_name)
        tasks_queue = await ch_read.get_queue(config.queue_name)
        return ex, tasks_queue, ch_write, ch_read


def _get_files(data, sig: inspect.Signature):
    args = {}
    for n, v in data.items():
        desc = sig.parameters.get(n)
        if desc is None:
            continue
        elif isinstance(desc.default, DescriptorBase) and desc.default.is_file:
            args[n] = desc.default.load_url(data[n])
        else:
            args[n] = v
    return args


def wrap_rabbit_s3(t: Target, msg: bytes, content_type: str):
    """
    Оборачиваем таргет как функцию, готовую принимать сообщения от rabbitmq
    Все файлы в таком случае будут ожидаться как ссылки на сетевое хранилище.
    Для s3 необходимо передавать presigned url
    Если функция возвращает файл, необходимо так же передать поле _ret_url, содержащее
    presigned url для загрузки итоговых данных.

    :param t:
    :return:
    """
    sig = inspect.signature(t.foo)

    if content_type == "json":
        data = orjson.loads(msg)
    else:
        raise TypeError(f"not compatible content_type {content_type}")
    if t.returns and t.returns.is_file and "_ret_url" not in data:
        raise ValueError(
            f"{t.name} returns file, ret_url must be provided in order to upload results"
        )
    args = _get_files(data, sig)
    ret = t.foo(**args)
    if t.returns:
        if t.returns.is_file:
            if isinstance(t.returns, JsonFile):
                if not t.returns.to_s3:
                    return orjson.dumps(ret)
            url = data["_ret_url"]
            parsed = urllib.parse.urlparse(url)
            *_, key = parsed.path.split("/")
            *_, ext = key.lower().split(".")
            ret = t.returns.to_file(ret, ext=ext)
            lg.debug("sending result to %s", url)
            with Session() as s:
                req = Request("PUT", url, data=ret.getbuffer())
                prepped = req.prepare()
                prepped.headers.pop("Content-Type", None)
                resp = s.send(prepped)

            if resp.status_code != 200:
                raise RuntimeError(
                    f"could not upload result to {url}, status: {resp.status_code}, info: {resp.content} {resp.request.headers}"
                )
            return b"ok"
        elif isinstance(t.returns, Dict) and content_type == "json":
            if not isinstance(ret, dict):
                raise TypeError(
                    f"return value is expected to be dict-like, but is {type(ret)} instead"
                )
            return orjson.dumps(ret)
        else:
            return b"ok"

    return


async def serve_rabbitmq(
    targets: typing.List[Target],
):
    exchange, queue, *_ = await get_exchange()
    targets = {t.name: t for t in targets}
    loop = asyncio.get_event_loop()
    sema = asyncio.Semaphore(config.n_workers)
    with concurrent.futures.ProcessPoolExecutor(config.n_workers) as pool:
        async with queue.iterator() as queue_iter:
            lg.info("started")
            await exchange.publish(
                Message(body=b"", headers={"type": "start"}), routing_key=""
            )
            async for message in queue_iter:
                async with message.process():
                    message: IncomingMessage
                    lg.debug(f"process message %s", message)
                    task_id: str = message.headers.get("task-id", None)
                    if task_id is None:
                        continue
                    await sema.acquire()  # не ставим больше задач чем можем обработать
                    asyncio.create_task(
                        execute_task(
                            targets=targets,
                            message=message,
                            loop=loop,
                            pool=pool,
                            exchange=exchange,
                            sema=sema,
                        )
                    )


async def execute_task(
    targets: typing.Dict[str, Target],
    message: IncomingMessage,
    loop: asyncio.AbstractEventLoop,
    pool: concurrent.futures.ProcessPoolExecutor,
    exchange: Exchange,
    sema: asyncio.Semaphore,
):
    task_id: str = message.headers.get("task-id", None)
    with set_task_id(task_id):
        try:
            target = targets.get(message.headers.get("target"))
            if target is None:
                raise KeyError(f"target with key {target} dows not exists")
            lg.debug("run %s", target)
            ret = await loop.run_in_executor(
                pool,
                wrap_rabbit_s3,
                target,
                message.body,
                message.content_type,
            )
        except Exception as exc:
            lg.exception("while processing %s", message)
            if message.content_type == "json":
                ret = orjson.dumps(
                    {
                        "error": True,
                        "trace": traceback.format_exc(),
                        "msg": str(exc),
                    }
                )
            else:
                ret = f"ERROR: {exc}".encode()
        finally:
            sema.release()
        lg.debug("sending results %s", ret)
        await exchange.publish(
            Message(ret, headers={"task-id": task_id, "type": "res"}), routing_key=""
        )
