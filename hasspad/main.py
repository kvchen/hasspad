#!/usr/bin/env python3

from rich.logging import RichHandler
from typing import List, Tuple

import asyncio
import click
import json
import keybow
import logging
import websockets

import color

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger(__file__)


class Hasspad:
    def __init__(self, uri: str, access_token: str, light_ids: List[str]):
        self.uri = uri
        self.access_token = access_token
        self.light_ids = light_ids

        self.request_id = 0
        self.request_lock = asyncio.Lock()

        self.light_states = [False for _ in light_ids]

    async def listen(self):
        try:
            keybow.set_all(255, 0, 0)
            keybow.show()

            async with websockets.connect(self.uri) as websocket:
                await self._authenticate(websocket)
                await self._initialize_states(websocket)

                handler = self._get_keypress_handler(websocket)
                keybow.on(handler=handler)

                await self._subscribe(websocket)

                while True:
                    message = json.loads(await websocket.recv())
                    if message['type'] == 'event' and message['event']['event_type'] == 'state_changed':
                        self._update_state(message['event']['data']['new_state'])

        except Exception as e:
            logger.exception(e)

    def _update_state(self, state):
        entity_id = state['entity_id']
        if entity_id not in self.light_ids:
            return

        light_rgb = self._get_light_rgb(state)

        logger.info(f"Setting {entity_id} state to {light_rgb}")

        index = self.light_ids.index(entity_id)
        self.light_states[index] = light_rgb is not None

        keybow.set_led(index, *[int(x) for x in light_rgb or (0, 0, 0)])
        keybow.show()

    async def _get_request_id(self):
        async with self.request_lock:
            self.request_id += 1
            return self.request_id

    async def _authenticate(self, websocket: websockets.client.WebSocketClientProtocol) -> None:
        # 2.1: Server sends auth_required

        auth_required_msg = json.loads(await websocket.recv())
        assert auth_required_msg['type'] == 'auth_required'

        # 2.2: Client sends auth

        await websocket.send(json.dumps({
            "type": "auth",
            "access_token": self.access_token,
        }))

        # 2.3: Server sends auth_ok or auth_invalid

        auth_msg = json.loads(await websocket.recv())
        if auth_msg['type'] == "auth_invalid":
            raise Exception(auth_msg['message'])

        assert auth_msg['type'] == 'auth_ok'

        logger.info("Authentication successful")

    async def _initialize_states(self, websocket: websockets.client.WebSocketClientProtocol):
        keybow.set_all(0, 0, 0)
        keybow.show()

        request_id = await self._get_request_id()

        await websocket.send(json.dumps({
            "id": request_id,
            "type": "get_states",
        }))

        init_response = json.loads(await websocket.recv())

        assert init_response['id'] == request_id
        assert init_response['success'] == True

        results = [
            result for result in init_response['result']
            if result['entity_id'] in self.light_ids
        ]

        for result in results:
            self._update_state(result)

    async def _subscribe(self, websocket: websockets.client.WebSocketClientProtocol) -> None:
        request_id = await self._get_request_id()

        await websocket.send(json.dumps({
            "id": request_id,
            "type": "subscribe_events",
            "event_type": "state_changed"
        }))

        subscribe_response = json.loads(await websocket.recv())

        assert subscribe_response['id'] == request_id
        assert subscribe_response['success'] == True

        logger.info("Subscribed to state changes")

    def _get_light_rgb(self, state):
        if state['state'] == 'off':
            return None

        attributes = state['attributes']
        if 'rgb_color' in attributes:
            return attributes['rgb_color']

        color_temp = attributes['color_temp']
        color_temp_kelvins = color.color_temperature_mired_to_kelvin(color_temp)
        return color.color_temperature_to_rgb(color_temp_kelvins)

    def _get_keypress_handler(self, websocket: websockets.client.WebSocketClientProtocol):
        async def toggle_light(index: int):
            service = 'turn_off' if self.light_states[index] else 'turn_on'
            light_id = self.light_ids[index]

            logger.info(f"Toggling light {light_id}")

            request_id = await self._get_request_id()

            await websocket.send(json.dumps({
                "id": request_id,
                "type": "call_service",
                "domain": "light",
                "service": service,
                "service_data": {
                    "entity_id": light_id
                }
            }))

        def handler(index, key_state):
            if key_state:  # Only handle release case
                return

            asyncio.run(toggle_light(index))

        return handler


@click.command()
@click.option('--uri', default="ws://homeassistant.local:8123/api/websocket")
@click.option('--access-token')
def main(uri: str, access_token: str) -> None:
    keybow.setup(list(reversed(keybow.MINI)))
    hasspad = Hasspad(
        uri=uri,
        access_token=access_token,
        light_ids=['light.desk_bias_light', 'light.desk_key_light']  # temporary, hardcoded
    )

    asyncio.run(hasspad.listen())


if __name__ == "__main__":
    main(auto_envvar_prefix='HASSPAD')
