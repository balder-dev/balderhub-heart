import balder

from .optical_heart_beat_feature import OpticalHeartBeatFeature

from ..scenario_features import StrapDockingFeature
from ..utils.optical_simulation import Command


class OpticalStrapDockingFeature(StrapDockingFeature):
    """Setup Level implementation for simulating the strap by using the optical heart beat feature"""

    class Heart(balder.VDevice):
        """vdevice of the heart"""
        heart = OpticalHeartBeatFeature()

    def put_on(self):
        self.Heart.heart.simulator.send_command(Command.DISABLE_FLASHING)

    def put_off(self):
        self.Heart.heart.simulator.send_command(Command.ENABLE_FLASHING)

    def is_attached(self):
        return not self.Heart.heart.simulator.send_command(Command.IS_FLASHING_ENABLED)
