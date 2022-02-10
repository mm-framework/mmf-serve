import logging

logging.basicConfig(level=logging.INFO)
import asyncio
import importlib
import os
import sys
import click
from mmf_meta.core import scan
from .config import config
from .rabbit_wrapper import serve_rabbitmq
from .logger import add_rabbit_handler, lg


@click.group()
def cli():
    sys.path.append(os.getcwd())
    return


@cli.command(name="serve-rabbit")
def serve_rabbit():
    """
    Прослушивание задач из очереди
    """
    lg.info("starting")
    loop = asyncio.get_event_loop()
    with add_rabbit_handler(loop=loop, lg=lg):
        script = config.main_script.replace(".py", "")
        lg.info("loading module %s", script)
        module = importlib.import_module(script)
        lg.info("module %s loaded", script)
        targets, _ = scan()
        lg.debug("targets loaded: %s", targets)
        loop.run_until_complete(
            serve_rabbitmq(
                targets=targets,
            )
        )


if __name__ == "__main__":
    cli()
