#!/usr/bin/env python3

import asyncio
import logging
from typing import TextIO

import click
import yaml
from rich.logging import RichHandler

from hasspad.config import HasspadConfig
from hasspad.hasspad import Hasspad

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)

logger = logging.getLogger(__file__)


@click.command()
@click.argument("config", type=click.File("r"))
def main(config: TextIO) -> None:
    hasspad = Hasspad(HasspadConfig(**yaml.safe_load(config)))
    asyncio.run(hasspad.listen())


if __name__ == "__main__":
    main(auto_envvar_prefix="HASSPAD")
