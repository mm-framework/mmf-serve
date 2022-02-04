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
    loop = asyncio.get_event_loop()
    with add_rabbit_handler(loop=loop, lg=lg):
        module = importlib.import_module(config.main_script.replace(".py", ""))
        targets, _ = scan()
        loop.run_until_complete(
            serve_rabbitmq(
                targets=targets,
            )
        )


if __name__ == "__main__":
    cli()
