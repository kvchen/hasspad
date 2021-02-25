from typing import Callable, Literal, Optional, Tuple, final

from pydantic import BaseModel
from pydantic.color import Color
from websockets.client import WebSocketClientProtocol

from .base import BaseEntityHandler, BaseEntityHandlerConfig, RawMessage


class LightEntityHandlerConfig(BaseEntityHandlerConfig):
    type: Literal["light"]

    def get_handler(self):
        return LightEntityHandler(self)


class LightEntityHandlerState(BaseModel):
    is_on: bool
    color: Color


class LightAttributes(BaseModel):
    rgb_color: Optional[Tuple[int, int, int]]


class LightEntityMessage(BaseModel):
    state: Literal["on", "off"]
    attributes: LightAttributes


class UpdateLightStateMessageServiceData(BaseModel):
    entity_id: str


class UpdateLightStateMessage(BaseModel):
    id: int
    service: Literal["turn_off", "turn_on"]
    service_data: UpdateLightStateMessageServiceData

    type = "call_service"
    domain = "light"


@final
class LightEntityHandler(
    BaseEntityHandler[LightEntityHandlerConfig, LightEntityHandlerState]
):
    @staticmethod
    def get_initial_state() -> LightEntityHandlerState:
        return LightEntityHandlerState(is_on=False, color=(0, 0, 0))

    @staticmethod
    def get_state_from_message(raw_message: RawMessage) -> LightEntityHandlerState:
        message = LightEntityMessage(**raw_message)
        return LightEntityHandlerState(
            is_on=message.state == "on",
            color=message.attributes.rgb_color or (255, 255, 255),
        )

    def on_state_change(self, set_color: Callable[[Color], None]) -> None:
        state = self.get_current_state()
        set_color(state.color if state.is_on else Color((0, 0, 0)))

    async def on_keypress(self, ws: WebSocketClientProtocol, message_id: int) -> None:
        state = self.get_current_state()
        message = UpdateLightStateMessage(
            id=message_id,
            service=("turn_off" if state.is_on else "turn_on"),
            service_data=UpdateLightStateMessageServiceData(
                entity_id=self.config.entity_id
            ),
        )
        await ws.send(message.json())
