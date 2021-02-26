from typing import List, Tuple, Callable

def setup(keymap: List[Tuple[int, int]]) -> None: ...
def set_led(index: int, r: int, g: int, b: int) -> None:
    """Set an led.

    :param index: 0-based index of key to set the LED for
    :param r, g, b: amount of Red, Green and Blue (0-255)

    """
    ...

def set_all(r: int, g: int, b: int) -> None:
    """Set all Keybow LEDs."""
    ...

def clear() -> None:
    """Clear Keybow LEDs."""
    ...

def show() -> None:
    """Update LEDs on Keybow."""
    ...

def on(
    index: int = ..., handler: Callable[[int, bool], None] = ...
) -> None:
    """Attach a handler to a Keybow key.

    Your handler should accept an index and a state argument.

    """
    ...
