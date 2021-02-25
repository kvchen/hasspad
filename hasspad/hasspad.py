import asyncio
import logging
from typing import Any, Callable, Dict, List, Literal, Mapping, Optional, Tuple, Type

import keybow
import websockets
from pydantic import BaseModel, SecretStr, ValidationError
from pydantic.color import Color

from hasspad.config import HasspadConfig
from hasspad.handlers.base import BaseEntityHandler, BaseEntityHandlerConfig

logger = logging.getLogger(__file__)


class AuthRequiredMessage(BaseModel):
    type: Literal["auth_required"]


class AuthTokenMessage(BaseModel):
    type: Literal["auth"] = "auth"
    access_token: SecretStr

    class Config:
        json_encoders: Mapping[
            Type[SecretStr], Callable[[SecretStr], Optional[str]]
        ] = {
            SecretStr: lambda v: v.get_secret_value() if v else None,
        }


class AuthResponseMessage(BaseModel):
    type: Literal["auth_ok", "auth_invalid"]
    message: Optional[str]


class GetStatesMessage(BaseModel):
    id: int
    type: Literal["get_states"] = "get_states"


class GetStatesResponseMessage(BaseModel):
    id: int
    type: Literal["result"]
    success: bool
    result: List[Dict[str, Any]]


class SubscribeEventsMessage(BaseModel):
    id: int
    type: Literal["subscribe_events"] = "subscribe_events"
    event_type: Literal["state_changed"] = "state_changed"


class SubscribeEventsResponseMessage(BaseModel):
    id: int
    type: Literal["result"]
    success: bool


class StateChangeData(BaseModel):
    new_state: Any


class StateChangeEvent(BaseModel):
    event_type: Literal["state_changed"]
    data: StateChangeData


class StateChangeEventMessage(BaseModel):
    type: Literal["event"]
    event: StateChangeEvent


EntityHandler = BaseEntityHandler[BaseEntityHandlerConfig, object]


class Hasspad:
    def __init__(self, config: HasspadConfig):
        self.config = config
        self.idx_to_handler, self.entity_id_to_idx = self._get_entity_handlers()

        self._message_id = 0
        self._message_id_lock = asyncio.Lock()

    async def listen(self):
        try:
            keybow.setup(self.config.size.get_keymap())

            async with websockets.connect(self.config.api.websocket_uri) as ws:
                await self._authenticate(ws)
                await self._initialize_entity_handlers(ws)
                await self._subscribe_to_state_changes(ws)

                keybow.on(handler=self._get_keybow_handler(ws))

                while True:
                    try:
                        message = StateChangeEventMessage.parse_raw(await ws.recv())
                    except ValidationError:
                        continue

                    new_state = message.event.data.new_state
                    self._handle_message(new_state["entity_id"], new_state)

        except Exception:
            keybow.set_all(255, 0, 0)
            keybow.show()
            raise

    async def _get_next_message_id(self):
        async with self._message_id_lock:
            self._message_id += 1
            return self._message_id

    def _get_entity_handlers(
        self,
    ) -> Tuple[Mapping[int, EntityHandler], Mapping[str, int],]:
        idx_to_handler = {}
        entity_id_to_idx = {}

        for idx, handler_config in enumerate(self.config.handlers):
            if handler_config is None:
                continue

            handler = handler_config.get_handler()

            idx_to_handler[idx] = handler
            entity_id_to_idx[handler_config.entity_id] = idx

        return idx_to_handler, entity_id_to_idx

    async def _authenticate(
        self, ws: websockets.client.WebSocketClientProtocol
    ) -> None:
        # 2.1: Server sends auth_required

        AuthRequiredMessage.parse_raw(await ws.recv())

        # 2.2: Client sends auth

        await ws.send(
            AuthTokenMessage(access_token=self.config.api.access_token).json()
        )

        # 2.3: Server sends auth_ok or auth_invalid

        auth_response_msg = AuthResponseMessage.parse_raw(await ws.recv())
        if auth_response_msg.type == "auth_invalid":
            raise Exception(auth_response_msg.message)

        logger.info("Authentication successful")

    async def _initialize_entity_handlers(
        self, ws: websockets.client.WebSocketClientProtocol
    ) -> None:
        request = GetStatesMessage(
            id=await self._get_next_message_id(),
        )
        await ws.send(request.json())

        response = GetStatesResponseMessage.parse_raw(await ws.recv())

        assert response.success == True

        for result in response.result:
            self._handle_message(result["entity_id"], result)

    async def _subscribe_to_state_changes(
        self, ws: websockets.client.WebSocketClientProtocol
    ) -> None:
        request = SubscribeEventsMessage(id=await self._get_next_message_id())
        await ws.send(request.json())

        response = SubscribeEventsResponseMessage.parse_raw(await ws.recv())

        assert response.success == True

    def _get_keybow_handler(
        self, ws: websockets.client.WebSocketClientProtocol
    ) -> Callable[[int, bool], None]:
        async def on_keypress(idx: int):
            entity_handler = self.idx_to_handler.get(idx)
            if not entity_handler:
                return

            message_id = await self._get_next_message_id()
            await entity_handler.on_keypress(ws, message_id)

        def handler(idx: int, key_state: bool):
            if key_state:
                return

            asyncio.run(on_keypress(idx))

        return handler

    def _set_key_color(self, idx: int, color: Color) -> None:
        logger.info(f"Setting key {idx} to {color}")
        keybow.set_led(idx, *color.as_rgb_tuple(alpha=False))
        keybow.show()

    def _handle_message(self, entity_id: str, message: Any) -> None:
        handler_idx = self.entity_id_to_idx.get(entity_id)
        if handler_idx is None:
            return None

        entity_handler = self.idx_to_handler[handler_idx]
        entity_handler.on_message(
            message, lambda color: self._set_key_color(handler_idx, color)
        )
