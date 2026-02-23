import time

import balder
from balder.connections import DCPowerConnection

from balderhub.heart.lib.scenario_features.bpm_value_reader_feature import BpmValueReaderFeature

from .base_scenario_env import BaseScenarioEnv
from ...lib.scenario_features import BaseTestCriteriaConfig


class ScenarioHeartRateCheck(BaseScenarioEnv):
    """
    Base test scenario validating the accuracy of the beat-per-minute value and it's update timing behavior
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
        reader = BpmValueReaderFeature()

    @balder.fixture('variation')
    def make_sure_has_skin_contact(self):
        """fixture that ensures skin contact before entering the variation"""
        yield from self.HeartRateSensor.strap.fixt_make_sure_to_be_attached()

    @balder.fixture('variation')
    def make_sure_device_powered_on(self, make_sure_has_skin_contact):  # pylint: disable=unused-argument
        """fixture that ensures that device is powered ob before entering the variation"""
        yield from self.BatterySim.sim.fixt_make_sure_device_is_powered_on()

    @balder.parametrize_by_feature("bpm", (HeartRateSensor, 'config', 'test_accuracy_of_bpms_for'))
    @balder.parametrize_by_feature("with_noice", (HeartRateSensor, 'config', 'test_noise_with_snr_of'))
    def test_normal_heart_rate(self, bpm, with_noice):
        """
        Base check that validates the transmitted heart beat and if it is updated within the expected timing

        :param bpm: PARAMETRIZED VALUE for the beats-per-minute frequency that should be applied
        :param with_noice: PARAMETRIZED VALUE if a noise should be added (None if no noise should be added, SNR in dB
                           otherwise)
        """
        if with_noice is not None:
            raise NotImplementedError

        self.HeartRateGiver.heart.start(bpm=bpm)
        try:
            self.HeartRateHost.reader.prepare()
            time.sleep(self.HeartRateSensor.config.max_bpm_change_update_time_sec)
            read_bpm = self.HeartRateHost.reader.read_last_bpm_value()

            expected_min_bpm = bpm * (1 - self.HeartRateSensor.config.allowed_plusminus_deviation_percent)
            expected_max_bpm = bpm * (1 + self.HeartRateSensor.config.allowed_plusminus_deviation_percent)

            assert expected_min_bpm < read_bpm < expected_max_bpm, \
                (f"the updated bpm was not read after "
                 f"{self.HeartRateSensor.config.max_bpm_change_update_time_sec} seconds or is not in expected "
                 f"range {bpm} +/- {self.HeartRateSensor.config.allowed_plusminus_deviation_percent * 100:.2f}% "
                 f"bpm (is {read_bpm})")
        finally:
            self.HeartRateHost.reader.cleanup()

    @balder.parametrize_by_feature('bpm_setting', (HeartRateSensor, 'config', 'test_update_time_for'))
    @balder.parametrize_by_feature("with_noice", (HeartRateSensor, 'config', 'test_noise_with_snr_of'))
    def test_update_time(
            self,
            bpm_setting: BaseTestCriteriaConfig.UpdateTimeTestConfig,
            with_noice
    ):  # pylint: disable=too-many-locals
        """
        test that validates that the sensor will handle frequency changes - it makes sure that every frequency is
        transmitted correctly within the expected maximal reaction time

        :param bpm_setting: PARAMETRIZED VALUE that describes the start and end time that should be tried
        :param with_noice: PARAMETRIZED VALUE if a noise should be added (None if no noise should be added, SNR in dB
                           otherwise)
        """
        if with_noice is not None:
            raise NotImplementedError

        time_to_wait_when_reached_sec = 30

        allowed_dev_percent = self.HeartRateSensor.config.allowed_plusminus_deviation_percent

        start_bpm = bpm_setting.start_bpm
        expected_min_start_bpm = start_bpm * (1 - allowed_dev_percent)
        expected_max_start_bpm = start_bpm * (1 + allowed_dev_percent)
        end_bpm = bpm_setting.end_bpm
        expected_min_end_bpm = start_bpm * (1 - allowed_dev_percent)
        expected_max_end_bpm = start_bpm * (1 + allowed_dev_percent)

        timeout_sec = bpm_setting.max_update_time_sec * 3

        start_time = time.perf_counter()
        self.HeartRateGiver.heart.start(bpm=start_bpm)

        try:
            self.HeartRateHost.reader.prepare()
            bpm_over_history = []

            while (time.perf_counter() - start_time) < timeout_sec:
                current_bpm = self.HeartRateHost.reader.read_last_bpm_value()
                bpm_over_history.append((time.perf_counter(), current_bpm))
                if expected_min_start_bpm <= current_bpm <= expected_max_start_bpm:
                    # value reached
                    __start_bpm_reached_at_timestamp = time.perf_counter()
                    break

            else:
                raise TimeoutError(f'unable to detect start bpm of {start_bpm} (+/-{allowed_dev_percent*100:.2f}%) '
                                   f'in reader within {timeout_sec} seconds')
            time.sleep(time_to_wait_when_reached_sec)

            change_time = time.perf_counter()
            self.HeartRateGiver.heart.start(bpm=end_bpm)
            while (time.perf_counter() - start_time) < timeout_sec:
                current_bpm = self.HeartRateHost.reader.read_last_bpm_value()
                bpm_over_history.append((time.perf_counter(), current_bpm))
                if expected_min_end_bpm <= current_bpm <= expected_max_end_bpm:
                    # value reached
                    end_bpm_reached_at_timestamp = time.perf_counter()
                    break
            else:
                raise TimeoutError(f'unable to detect start bpm of {start_bpm} (+/-{allowed_dev_percent*100:.2f}%) '
                                   f'in reader within {timeout_sec} seconds - received: {bpm_over_history}')


            assert (end_bpm_reached_at_timestamp - change_time) < bpm_setting.max_update_time_sec, \
                (f"time to update bpm from {start_bpm} to {end_bpm} needed "
                 f"{(end_bpm_reached_at_timestamp - change_time)} seconds "
                 f"(expectation was below {bpm_setting.max_update_time_sec} seconds)")

            time.sleep(time_to_wait_when_reached_sec)

            # TODO validate history -> should not go down and stay within the allowed range
            constant_with_start_bpm = [
                bpm for ts, bpm in bpm_over_history if start_time + bpm_setting.max_update_time_sec < ts < change_time
            ]

            assert len(constant_with_start_bpm) > 0, "received nothing after set start bpm"

            assert expected_min_start_bpm <= min(constant_with_start_bpm) <= expected_max_start_bpm, \
                (f"detect some bpm after the start bpm should be detected constantly that are not within the expected "
                 f"range of {expected_min_start_bpm}-{expected_max_start_bpm} "
                 f"({start_bpm} +/-{allowed_dev_percent*100:.2f}%): {constant_with_start_bpm}")

            assert expected_min_start_bpm <= max(constant_with_start_bpm) <= expected_max_start_bpm, \
                (f"detect some bpm after the start bpm should be detected constantly that are not within the expected "
                 f"range of {expected_min_start_bpm}-{expected_max_start_bpm} "
                 f"({start_bpm} +/-{allowed_dev_percent * 100:.2f}%): {constant_with_start_bpm}")

            constant_with_end_bpm = [
                bpm for ts, bpm in bpm_over_history if change_time + bpm_setting.max_update_time_sec < ts
            ]

            assert len(constant_with_end_bpm) > 0, "received nothing after set end bpm"

            assert expected_min_end_bpm <= min(constant_with_end_bpm) <= expected_max_end_bpm, \
                (f"detect some bpm after the end bpm should be detected constantly that are not within the expected "
                 f"range of {expected_min_end_bpm}-{expected_max_end_bpm} "
                 f"({end_bpm} +/-{allowed_dev_percent*100:.2f}%): {constant_with_end_bpm}")

            assert expected_min_end_bpm <= max(constant_with_end_bpm) <= expected_max_end_bpm, \
                (f"detect some bpm after the end bpm should be detected constantly that are not within the expected "
                 f"range of {expected_min_end_bpm}-{expected_max_end_bpm} "
                 f"({end_bpm} +/-{allowed_dev_percent * 100:.2f}%): {constant_with_end_bpm}")
        finally:
            self.HeartRateHost.reader.cleanup()
