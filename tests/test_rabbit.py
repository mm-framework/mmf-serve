import logging

import async_timeout

logging.basicConfig(level=logging.DEBUG)

import asyncio
import importlib
import json

import aioboto3
import pytest
from mmf_meta.core import TARGETS, scan
from mmf_serve.rabbit_wrapper import serve_rabbitmq, get_exchange
from mmf_serve.config import config
from aio_pika import (
    connect_robust,
    Connection,
    Message,
    IncomingMessage,
    Queue,
    Channel,
)


@pytest.fixture(scope="package")
def targets():
    module = importlib.import_module("ex")
    targets, arts = scan()
    yield targets


@pytest.fixture(scope="package")
async def s3():
    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url="http://localhost:9000",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
    ) as s3:
        yield s3


@pytest.fixture(scope="package")
async def prepped_urls(s3):
    dwn = await s3.generate_presigned_url(
        "get_object", Params={"Bucket": "mmf", "Key": "test.xlsx"}, ExpiresIn=3600
    )
    up = await s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": "mmf", "Key": "res.xlsx"},
        ExpiresIn=3600,
    )
    # up = await s3.generate_presigned_post("mmf", "res.xlsx", ExpiresIn=3600)
    yield dwn, up


@pytest.fixture(scope="package")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="package")
def conf():
    config.queue_name = "test_task"
    config.exchange_name = "test_results"


@pytest.fixture(scope="package")
def add_handler(event_loop):
    from mmf_serve.logger import add_rabbit_handler, lg

    with add_rabbit_handler(event_loop, lg):
        yield


@pytest.fixture(scope="package")
async def prep_rabbit(conf, event_loop, add_handler):

    ex, que, ch_read, ch_write = await get_exchange()
    qres: Queue = await ch_write.declare_queue(durable=False, exclusive=True)
    await qres.bind(ex)
    yield ex, que, qres, ch_read, ch_write


@pytest.fixture
def data(prepped_urls):
    dwn, up = prepped_urls
    data = {"df": dwn}
    data = json.dumps(data)
    print(data)
    yield data.encode(), up


@pytest.mark.asyncio
async def test_rabbit(prep_rabbit, targets, data):

    ex, que, qres, ch_read, ch_write = prep_rabbit
    data, up = data

    task = asyncio.create_task(
        serve_rabbitmq(
            targets=targets,
        )
    )

    await ch_write.default_exchange.publish(
        Message(
            data,
            headers={"target": "score", "task-id": "12345", "ret_url": up},
            content_type="json",
        ),
        routing_key=que.name,
    )
    try:
        has_start = False
        has_logs = False
        async with async_timeout.timeout(60):
            async with qres.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        message: IncomingMessage
                        if message.headers["type"] == "start":
                            has_start = True
                            continue
                        elif message.headers["type"] == "res":
                            assert message.body == b"ok"
                            return
                        elif message.headers["type"] == "log":
                            has_logs = True
        assert has_start
        assert has_logs
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
