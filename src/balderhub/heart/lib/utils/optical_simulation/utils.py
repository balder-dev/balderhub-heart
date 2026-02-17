import dataclasses
import enum


class Command(enum.Enum):
    """enum with all possible commands"""
    START = enum.auto()
    STOP = enum.auto()
    SET_BPM = enum.auto()
    GET_BPM = enum.auto()
    IS_ACTIVE = enum.auto()
    ENABLE_FLASHING = enum.auto()
    DISABLE_FLASHING = enum.auto()
    IS_FLASHING_ENABLED = enum.auto()
    QUIT = enum.auto()


@dataclasses.dataclass
class ColorConfiguration:
    """color configuration dataclass that can be adjusted to the requirements of the DUT"""
    RED_MIN = 0x5F
    RED_MAX = 0xBE
    GREEN_MIN = 0x5F
    GREEN_MAX = 0xBE
    BLUE_MIN = 0x3C
    BLUE_MAX = 0x3C

    def get_color(self, for_alpha: float) -> str:
        """
        Returns the corresponding color for the given alpha value and based on the min/max values of the color
        configuration

        :param for_alpha: current alpha value that should be applied
        :return: the color string
        """
        if not 0 <= for_alpha <= 1:
            raise ValueError('for_alpha must be between 0 and 1')
        red = int((self.RED_MAX - self.RED_MIN) * for_alpha + self.RED_MIN)
        green = int((self.GREEN_MAX - self.GREEN_MIN) * for_alpha + self.GREEN_MIN)
        blue = int((self.BLUE_MAX - self.BLUE_MIN) * for_alpha + self.BLUE_MIN)
        return f'#{red:02x}{green:02x}{blue:02x}'
