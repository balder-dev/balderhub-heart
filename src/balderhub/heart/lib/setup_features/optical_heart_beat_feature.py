from typing import Union

from balderhub.heart.lib.scenario_features.heart_beat_feature import HeartBeatFeature
from balderhub.heart.lib.utils.optical_simulation import ColorConfiguration, Command, TkinterOpticalHeartBeatSimulation


class OpticalHeartBeatFeature(HeartBeatFeature):
    """
    Setup Level feature implementation of the :class:`balderhub.heart.lib.scenario_features.HeartBeatFeature` for
    simulating a heart beat optical with the users monitor
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._simulator: Union[TkinterOpticalHeartBeatSimulation, None] = None

    @property
    def position(self) -> tuple[int, int]:
        """
        :return: returns a tuple (x, y) with the position of the heart beat simulation and the users monitor
        """
        return 100, 100

    @property
    def size(self) -> tuple[int, int]:
        """
        :return: returns a tuple (width, height) with the size of the heart beat simulation and the users monitor
        """
        return 300, 300

    @property
    def color_config(self) -> ColorConfiguration:
        """
        :return: the color configuration object describing the optical visualization
        """
        return ColorConfiguration()

    @property
    def simulator(self) -> Union[TkinterOpticalHeartBeatSimulation, None]:
        """
        :return: returns the current active simulator instance or None if no simulator is active
        """
        return self._simulator

    def start_application(self) -> None:
        """
        This method starts the application. It should be called before entering the test.
        """
        if self._simulator is not None:
            raise ValueError('can not start process because another one is still active')
        self._simulator = TkinterOpticalHeartBeatSimulation(
            position=self.position,
            size=self.size,
            color_config=self.color_config
        )
        self._simulator.open_window()

    def shutdown_application(self) -> None:
        """
        This method shuts the application down. It should be called after leaving the test.
        """
        if self._simulator is None:
            return
        self._simulator.close_window()
        self._simulator = None


    def start(self, bpm: float):
        self.simulator.send_command(Command.SET_BPM, bpm=bpm)
        self.simulator.send_command(Command.START)

    def stop(self):
        self.simulator.send_command(Command.STOP)

    def get_current_active_bpm(self) -> Union[float, None]:
        if self.simulator.send_command(Command.IS_ACTIVE):
            return self.simulator.send_command(Command.GET_BPM)
        return None
