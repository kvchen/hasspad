import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, TypeVar, final

from pydantic import BaseModel
from pydantic.color import Color
from websockets.client import WebSocketClientProtocol

logger = logging.getLogger(__file__)


class BaseEntityHandlerConfig(BaseModel):
    entity_id: str


RawMessage = Any

Config = TypeVar("Config", bound=BaseEntityHandlerConfig, covariant=True)
State = TypeVar("State", covariant=True)


class BaseEntityHandler(Generic[Config, State], ABC):
    @final
    def __init__(self, config: Config):
        self.config: Config = config

        self._state: State = self.get_initial_state()

    @staticmethod
    @abstractmethod
    def get_initial_state() -> State:
        """
        Used to initialize local state before any messages are received.
        """
        pass

    @staticmethod
    @abstractmethod
    def get_state_from_message(raw_message: RawMessage) -> State:
        pass

    @abstractmethod
    def on_state_change(self, set_color: Callable[[Color], None]) -> None:
        """
        Performs a side-effect when the state is changed.
        This should generally be used to change the color of the keypad light.
        """
        pass

    @abstractmethod
    async def on_keypress(self, ws: WebSocketClientProtocol, message_id: int) -> None:
        pass

    def get_current_state(self) -> State:
        return self._state

    def on_message(
        self, raw_message: RawMessage, set_color: Callable[[Color], None]
    ) -> None:
        logger.info(f"Entity {self.config.entity_id} updated")
        self._state = self.get_state_from_message(raw_message)
        self.on_state_change(set_color)
