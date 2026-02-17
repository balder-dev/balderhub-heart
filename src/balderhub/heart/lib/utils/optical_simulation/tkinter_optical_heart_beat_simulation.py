from typing import Any
import multiprocessing

from balderhub.heart.lib.utils.optical_simulation.process_func import process_target_func
from balderhub.heart.lib.utils.optical_simulation.utils import ColorConfiguration, Command


class TkinterOpticalHeartBeatSimulation:
    """
    Simulator class that creates an own tkinter process to simulate heart beat behavior for optical sensors.
    """

    def __init__(
            self,
            position: tuple[int, int],
            size: tuple[int, int] = (200, 200),
            color_config: ColorConfiguration = None
    ) -> None:
        """
        Instantiates a new application that simulates the optical heart beat behavior for optical sensors.
        :param position: tuple with x, y position the window should be placed on users display
        :param size: tuple with width, height the window should be
        :param color_config: optional overwritten color configuration how the window should behave
        """
        self._position = position
        self._size = size

        self._color_config = color_config if color_config is not None else ColorConfiguration()

        self._process = None
        self._to_tkinter_queue = multiprocessing.Queue()
        self._to_main_queue = multiprocessing.Queue()

    def send_command(self, cmd: Command, timeout_sec: float = 10, **kwargs) -> Any:
        """
        Method that sends commands to the graphical process
        :param cmd: command to send
        :param timeout_sec: timeout to wait for confirmation
        :return: returns the confirmation value
        """
        self._to_tkinter_queue.put((cmd, kwargs))
        response = self._to_main_queue.get(timeout=timeout_sec)
        return response

    def open_window(self) -> None:
        """
        This method opens the window and starts the process
        """
        if self._process is not None:
            raise ValueError('another process is already running')
        self._process = multiprocessing.Process(
            target=process_target_func,
            args=(self._to_main_queue, self._to_tkinter_queue, self._position, self._size, self._color_config)
        )
        self._process.start()

    def close_window(self) -> None:
        """
        This method closes the window and stops the process
        """
        self._to_tkinter_queue.put((Command.QUIT, {}))
        self._process.join()
        self._process = None
