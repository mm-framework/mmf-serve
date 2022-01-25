import logging

logging.basicConfig(level=logging.DEBUG)

import asyncio
import importlib
import json

import aioboto3
import pytest
from mmf_meta.core import TARGETS, scan
from mmf_serve.rabbit_wrapper import serve_rabbitmq
from mmf_serve.config import config
from aio_pika import connect_robust, Connection, Message, IncomingMessage


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
    up = await s3.generate_presigned_post("mmf", "res.xlsx", ExpiresIn=3600)
    yield dwn, up


@pytest.fixture(scope="package")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="package")
async def prep_rabbit():
    con: Connection = await connect_robust(config.rabbit.con_string)
    ch = await con.channel()
    ch2 = await con.channel()
    q_tasks = await ch.declare_queue("test_task")
    send_results = await ch.declare_exchange("test_send_results")
    send_tasks = await ch2.declare_exchange("test_send_tasks")
    await q_tasks.bind(send_tasks.name, routing_key="")
    q_results = await ch2.declare_queue("test_results")
    await q_results.bind(send_results.name, routing_key="")

    yield q_tasks, q_results, send_results, send_tasks


@pytest.fixture
def data(prepped_urls):
    dwn, up = prepped_urls
    data = {"_ret_url": up, "df": dwn}
    data = json.dumps(data)
    print(data)
    yield data.encode()


@pytest.mark.asyncio
async def test_rabbit(prep_rabbit, targets, data):

    q_tasks, q_results, send_results, send_tasks = prep_rabbit
    task = asyncio.create_task(
        serve_rabbitmq(
            n_proc=1,
            queue_name=q_tasks.name,
            targets=targets,
            rabbit_params=config.rabbit.dict(),
            results_exchange=send_results.name,
        )
    )

    await send_tasks.publish(
        Message(
            data, headers={"target": "score", "task-id": "12345"}, content_type="json"
        ),
        routing_key="",
    )
    try:
        async with q_results.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    message: IncomingMessage
                    assert message.body == b"ok"
                    return
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
