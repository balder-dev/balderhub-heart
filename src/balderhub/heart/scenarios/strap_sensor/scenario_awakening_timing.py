import logging
import time

import balder
from balder.connections import DCPowerConnection


from balderhub.battery.lib.scenario_features import DeviceActivityFeature
from .base_scenario_env import BaseScenarioEnv

logger = logging.getLogger(__name__)


class ScenarioAwakeningTiming(BaseScenarioEnv):
    """Test scenario that validates the timing for going to sleep and awake again depending on heart beat and if the
    strap is attached"""

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
        activity = DeviceActivityFeature()

    @balder.fixture('variation')
    def make_sure_device_powered_on(self):
        """fixture that ensures that device is powered ob before entering the variation"""
        yield from self.BatterySim.sim.fixt_make_sure_device_is_powered_on()

    @balder.fixture('variation')
    def make_sure_has_no_skin_contact_for_variation(self):
        """fixture that ensures no skin contact before entering the variation"""
        yield from self.HeartRateSensor.strap.fixt_make_sure_to_be_not_attached(restore_entry_state=True)

    @balder.fixture('testcase')
    def make_sure_has_no_skin_contact(self):
        """fixture that ensures no skin contact before every testcase"""
        yield from self.HeartRateSensor.strap.fixt_make_sure_to_be_not_attached(restore_entry_state=False)

    @balder.fixture('testcase')
    def make_sure_to_be_not_active_anymore(self, make_sure_has_no_skin_contact):  # pylint: disable=unused-argument
        """fixture that ensures that sensor is not active before every testcase"""
        timeout = self.HeartRateSensor.config.time_to_sleep_after_skin_contact_loss
        self.HeartRateHost.activity.wait_to_be_inactive(timeout_sec=timeout)

    # every test will be entered without skin contact and freshly restarted device

    @balder.parametrize('with_bpm', [60, 120])
    @balder.parametrize_by_feature("with_noice", (HeartRateSensor, 'config', 'test_noise_with_snr_of'))
    def test_auto_awake_with_contact_and_signal(self, with_bpm, with_noice):
        """
        test that validates that the sensor will automatically awake as soon as the heart rate sensor is in contact
        with the skin and a valid heart beat is aligned
        """
        if with_noice is not None:
            raise NotImplementedError

        assert not self.HeartRateSensor.strap.is_attached(), "sensor is already attached"
        self.HeartRateGiver.heart.start(with_bpm)

        # make sure that sensor is not active
        assert not self.HeartRateHost.activity.is_active(), "sensor is already activated before strap was attached"

        start_time = time.perf_counter()
        self.HeartRateSensor.strap.put_on()

        expected_awakening_time_sec = self.HeartRateSensor.config.timeout_awakening_sec
        max_timeout = expected_awakening_time_sec * 5  # wait max this time to check if

        while time.perf_counter() - start_time < max_timeout:
            if self.HeartRateHost.activity.is_active():
                active_after_sec = time.perf_counter() - start_time
                break
        else:
            raise TimeoutError(f'sensor was not powered on within {max_timeout} seconds')

        assert active_after_sec <= expected_awakening_time_sec, \
            (f"sensor was not awakened within {expected_awakening_time_sec} seconds - it took around "
             f"{active_after_sec} seconds")

    @balder.parametrize('with_noice', [True, False])
    def test_auto_awake_with_contact_but_without_signal(self, with_noice):
        """
        test that validates that the sensor will automatically awake as soon as the heart rate sensor is in contact
        with the skin
        """
        if with_noice is not None:
            raise NotImplementedError

        assert not self.HeartRateSensor.strap.is_attached(), "sensor is already attached"
        self.HeartRateGiver.heart.stop()

        # make sure that sensor is not active
        assert not self.HeartRateHost.activity.is_active(), "sensor is already activated before strap was attached"

        start_time = time.perf_counter()
        self.HeartRateSensor.strap.put_on()

        expected_awakening_time_sec = self.HeartRateSensor.config.timeout_awakening_sec
        max_timeout = expected_awakening_time_sec * 5  # wait max this time to check if

        while time.perf_counter() - start_time < max_timeout:
            if self.HeartRateHost.activity.is_active():
                active_after_sec = time.perf_counter() - start_time
                break
        else:
            raise TimeoutError(f'sensor was not powered on within {max_timeout} seconds')

        assert active_after_sec <= expected_awakening_time_sec, \
            f"sensor was not awakened within {expected_awakening_time_sec} seconds, it took {active_after_sec} seconds"

        # now check if it will be disabled after `time_to_sleep_after_no_signal`
        expected_go_to_sleep_time_sec = self.HeartRateSensor.config.time_to_sleep_after_no_signal
        max_timeout = expected_go_to_sleep_time_sec * 2  # wait max this time to check if

        while time.perf_counter() - start_time < max_timeout:
            if not self.HeartRateHost.activity.is_active():
                inactive_after_sec = time.perf_counter() - start_time
                break
        else:
            raise TimeoutError(f'sensor is not go back to sleep within {max_timeout} seconds')

        assert inactive_after_sec <= expected_go_to_sleep_time_sec, \
            f"sensor was not awakened within {expected_go_to_sleep_time_sec} seconds"
