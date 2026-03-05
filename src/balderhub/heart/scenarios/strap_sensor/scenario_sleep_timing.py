import time
import logging
import balder

from balder.connections import DCPowerConnection
import balderhub.battery.lib.scenario_features

from .base_scenario_env import BaseScenarioEnv

logger = logging.getLogger(__name__)


class ScenarioSleepTiming(BaseScenarioEnv):
    """
    Test scenario that validates the timing for going to sleep depending on heart beat and if the strap is attached
    """

    class HeartRateGiver(BaseScenarioEnv.HeartRateGiver):
        """simulation device that initiate the hear rate"""

    @balder.connect(HeartRateGiver, over_connection=balder.Connection)  # pylint: disable=undefined-variable
    class HeartRateSensor(BaseScenarioEnv.HeartRateSensor):
        """device detecting the row heart rate"""

    @balder.connect(HeartRateSensor, over_connection=DCPowerConnection)  # pylint: disable=undefined-variable
    class BatterySim(BaseScenarioEnv.BatterySim):
        """device simulating the battery"""

    @balder.connect(HeartRateSensor, over_connection=balder.Connection)  # pylint: disable=undefined-variable
    class HeartRateHost(BaseScenarioEnv.HeartRateHost):
        """device receiving the heart rate data"""
        activity = balderhub.battery.lib.scenario_features.DeviceActivityFeature()

    @balder.fixture('variation')
    def make_sure_device_powered_on(self):
        """fixture that ensures that the device is powered obn before entering the variation"""
        yield from self.BatterySim.sim.fixt_make_sure_device_is_powered_on()

    @balder.fixture('variation')
    def make_sure_to_has_heartbeat(self):
        """fixture that ensures a valid heart beat before entering the variation"""
        yield from self.HeartRateGiver.heart.fixt_make_sure_heart_beat_established()

    @balder.fixture('testcase')
    def make_sure_has_skin_contact(self):
        """fixture that ensures skin contact before entering the testcase"""
        yield from self.HeartRateSensor.strap.fixt_make_sure_to_be_attached()

    @balder.fixture('testcase')
    def prepare_activity_feature(self):
        """prepares the activity feature for checking its activity"""
        self.HeartRateHost.activity.prepare()
        yield
        self.HeartRateHost.activity.cleanup()

    @balder.fixture('testcase')
    def make_sure_to_be_active(
            self,
            make_sure_has_skin_contact,
            prepare_activity_feature
    ):  # pylint: disable=unused-argument
        """fixture that ensures that sensor is not active before every testcase"""
        self.HeartRateHost.activity.wait_to_be_active(timeout_sec=self.HeartRateSensor.config.timeout_awakening_sec)

    # every test will be entered with skin contact

    @balder.parametrize('with_noice', [True, False])
    def test_sleep_after_losing_heartbeat(self, with_noice):  # pylint: disable=unused-argument
        """
        Test that validates that device stops sending messages / closes the connection as soon as the heart rate
        sensor detects no heart beats anymore
        """
        assert self.HeartRateSensor.strap.is_attached(), "sensor is not attached"
        assert self.HeartRateGiver.heart.get_current_active_bpm() is not None, \
            "heart beat needs to be active before we can measure go-to-sleep time"

        # make sure that sensor is active
        assert self.HeartRateHost.activity.is_active(), "sensor needs to be active before we can remove heart beat"

        start_time = time.perf_counter()
        self.HeartRateGiver.heart.stop()

        expected_go_to_sleep_time_sec = self.HeartRateSensor.config.time_to_sleep_after_no_signal
        if expected_go_to_sleep_time_sec is not None:
            logger.info(f'it is expected that the device goes back to sleep within {expected_go_to_sleep_time_sec} '
                        f'seconds after there was no valid signal detected')

            # now check if it will be disabled after `time_to_sleep_after_no_signal`

            max_timeout = expected_go_to_sleep_time_sec * 2  # wait max this time to check if

            while time.perf_counter() - start_time < max_timeout:
                if not self.HeartRateHost.activity.is_active():
                    inactive_after_sec = time.perf_counter() - start_time
                    break
            else:
                raise TimeoutError(f'sensor is not go back to sleep within {max_timeout} seconds')

            assert inactive_after_sec <= expected_go_to_sleep_time_sec, \
                f"sensor was not awakened within {expected_go_to_sleep_time_sec} seconds"
        else:
            wait_time_sec = self.HeartRateSensor.config.time_to_sleep_after_skin_contact_loss * 2
            logger.info(f'it is expected that the device goes not to sleep when no signal is detected, but the skin '
                        f'contact remains - wait for up to {wait_time_sec} seconds and validate that')
            while time.perf_counter() - start_time < wait_time_sec:
                if not self.HeartRateHost.activity.is_active():
                    inactive_after_sec = time.perf_counter() - start_time
                    raise ValueError(f'sensor unexpectatly goes back to sleep after {inactive_after_sec} seconds '
                                     f'while getting no signal, but still have skin contact')
            logger.info('sensor is still active ')

    def test_sleep_after_losing_skin_contact(self):
        """
        Test that validates that device stops sending messages / closes the connection as soon as the heart rate
        sensor does not have skin contact anymore
        """
        assert self.HeartRateSensor.strap.is_attached(), \
            "sensor needs to be attached before we can remove it to measure go-to-sleep time"
        assert self.HeartRateGiver.heart.get_current_active_bpm() is not None, \
            "heart beat needs to be active before we can measure go-to-sleep time"

        # make sure that sensor is active
        assert self.HeartRateHost.activity.is_active(), "sensor needs to be active before we can remove heart beat"

        start_time = time.perf_counter()
        self.HeartRateSensor.strap.put_off()

        expected_go_to_sleep_time_sec = self.HeartRateSensor.config.time_to_sleep_after_skin_contact_loss
        max_timeout = expected_go_to_sleep_time_sec * 2  # wait max this time to check if

        while time.perf_counter() - start_time < max_timeout:
            if not self.HeartRateHost.activity.is_active():
                inactive_after_sec = time.perf_counter() - start_time
                break
        else:
            raise TimeoutError(f'sensor is not go back to sleep within {max_timeout} seconds')

        assert inactive_after_sec <= expected_go_to_sleep_time_sec, \
            f"sensor was not going to sleep within {expected_go_to_sleep_time_sec} seconds"
