from enum import Enum
from typing import List, Tuple, Union, cast

import keybow
from pydantic import BaseModel, SecretStr, stricturl, validator

from hasspad.handlers.light import LightEntityHandlerConfig


class APIConfig(BaseModel):
    websocket_uri: stricturl(allowed_schemes={"ws", "wss"})
    access_token: SecretStr


class KeybowSize(Enum):
    MINI = "mini"
    FULL = "full"

    def get_keymap(self) -> List[Tuple[int, int]]:
        if self == KeybowSize.MINI:
            return keybow.MINI
        else:
            return keybow.FULL

    def num_keys(self) -> int:
        return len(self.get_keymap())


HasspadHandlerConfig = Union[LightEntityHandlerConfig]


class HasspadConfig(BaseModel):
    api: APIConfig
    size: KeybowSize
    handlers: List[Union[None, HasspadHandlerConfig]]

    @validator("handlers")
    def handler_count_must_match_size(
        cls, handlers: List[HasspadHandlerConfig], values
    ):
        size = cast(KeybowSize, values["size"])

        if size.num_keys() != len(handlers):
            raise ValueError(
                f"{size} should have {size.num_keys()} handlers, {len(handlers)} provided"
            )

        return handlers
