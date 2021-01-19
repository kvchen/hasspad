# These utilities are taken from the Home Assistant source code.

import math
from typing import Tuple


def color_temperature_to_rgb(
    color_temperature_kelvin: float,
) -> Tuple[float, float, float]:
    """
    Return an RGB color from a color temperature in Kelvin.

    This is a rough approximation based on the formula provided by T. Helland
    http://www.tannerhelland.com/4435/convert-temperature-rgb-algorithm-code/
    """
    # range check
    if color_temperature_kelvin < 1000:
        color_temperature_kelvin = 1000
    elif color_temperature_kelvin > 40000:
        color_temperature_kelvin = 40000

    tmp_internal = color_temperature_kelvin / 100.0

    red = _get_red(tmp_internal)

    green = _get_green(tmp_internal)

    blue = _get_blue(tmp_internal)

    return red, green, blue


def _bound(color_component: float, minimum: float = 0, maximum: float = 255) -> float:
    """
    Bound the given color component value between the given min and max values.

    The minimum and maximum values will be included in the valid output.
    i.e. Given a color_component of 0 and a minimum of 10, the returned value
    will be 10.
    """
    color_component_out = max(color_component, minimum)
    return min(color_component_out, maximum)


def _get_red(temperature: float) -> float:
    """Get the red component of the temperature in RGB space."""
    if temperature <= 66:
        return 255
    tmp_red = 329.698727446 * math.pow(temperature - 60, -0.1332047592)
    return _bound(tmp_red)


def _get_green(temperature: float) -> float:
    """Get the green component of the given color temp in RGB space."""
    if temperature <= 66:
        green = 99.4708025861 * math.log(temperature) - 161.1195681661
    else:
        green = 288.1221695283 * math.pow(temperature - 60, -0.0755148492)
    return _bound(green)


def _get_blue(temperature: float) -> float:
    """Get the blue component of the given color temperature in RGB space."""
    if temperature >= 66:
        return 255
    if temperature <= 19:
        return 0
    blue = 138.5177312231 * math.log(temperature - 10) - 305.0447927307
    return _bound(blue)


def color_temperature_mired_to_kelvin(mired_temperature: float) -> float:
    """Convert absolute mired shift to degrees kelvin."""
    return math.floor(1000000 / mired_temperature)
