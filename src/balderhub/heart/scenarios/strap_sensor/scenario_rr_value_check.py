import time

import balder
from balder.connections import DCPowerConnection

from balderhub.heart.lib.scenario_features.rr_value_reader_feature import RRValueReaderFeature

from .base_scenario_env import BaseScenarioEnv
from ...lib.scenario_features import BaseTestCriteriaConfig


class ScenarioRRValueCheck(BaseScenarioEnv):
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
        reader = RRValueReaderFeature()

    @balder.fixture('variation')
    def make_sure_has_skin_contact(self):
        """fixture that ensures no skin contact before every testcase"""
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
        self.HeartRateGiver.heart.start(bpm=bpm, add_noise_with_snr_of=with_noice)
        try:
            self.HeartRateHost.reader.prepare()
            expected_rr_value_sec = 60 / bpm

            allowed_dev_percent = self.HeartRateSensor.config.allowed_plusminus_deviation_percent
            expected_min_rr = expected_rr_value_sec * (1 - allowed_dev_percent)
            expected_max_rr = expected_rr_value_sec * (1 + allowed_dev_percent)

            time.sleep(self.HeartRateSensor.config.max_rr_change_update_time_sec)
            read_rrvalue = self.HeartRateHost.reader.read_last_rr_value_in_sec()

            assert expected_min_rr < read_rrvalue < expected_max_rr, \
                (f"the updated rr was not established after {self.HeartRateSensor.config.max_rr_change_update_time_sec}"
                 f" seconds or is not in expected range {expected_rr_value_sec} +/- {allowed_dev_percent * 100:.2f}% "
                 f"sec (is {read_rrvalue} sec)")
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

        time_to_wait_when_reached_sec = 30

        allowed_dev_percent = self.HeartRateSensor.config.allowed_plusminus_deviation_percent

        start_bpm = bpm_setting.start_bpm
        expected_start_rr_sec = 60 / start_bpm
        expected_min_start_rr = expected_start_rr_sec * (1 - allowed_dev_percent)
        expected_max_start_rr = expected_start_rr_sec * (1 + allowed_dev_percent)
        end_bpm = bpm_setting.end_bpm
        expected_end_rr_sec = 60 / end_bpm
        expected_min_end_rr = expected_end_rr_sec * (1 - allowed_dev_percent)
        expected_max_end_rr = expected_end_rr_sec * (1 + allowed_dev_percent)

        timeout_sec = self.HeartRateSensor.config.max_rr_change_update_time_sec * 3

        start_time = time.perf_counter()
        self.HeartRateGiver.heart.start(bpm=start_bpm, add_noise_with_snr_of=with_noice)

        try:
            rr_over_history = []
            self.HeartRateHost.reader.prepare()

            while (time.perf_counter() - start_time) < timeout_sec:
                current_rr_sec = self.HeartRateHost.reader.read_last_rr_value_in_sec()
                rr_over_history.append((time.perf_counter(), current_rr_sec))
                if expected_min_start_rr <= current_rr_sec <= expected_max_start_rr:
                    # value reached
                    __start_rr_reached_at_timestamp = time.perf_counter()
                    break

            else:
                raise TimeoutError(
                    f'unable to detect start rr of {expected_start_rr_sec} (+/-{allowed_dev_percent*100:.2f}%) '
                    f'in reader within {timeout_sec} seconds')
            time.sleep(time_to_wait_when_reached_sec)

            change_time = time.perf_counter()
            self.HeartRateGiver.heart.start(bpm=end_bpm, add_noise_with_snr_of=with_noice)
            while (time.perf_counter() - start_time) < timeout_sec:
                current_rr_sec = self.HeartRateHost.reader.read_last_rr_value_in_sec()
                rr_over_history.append((time.perf_counter(), current_rr_sec))
                if expected_min_end_rr <= current_rr_sec <= expected_max_end_rr:
                    # value reached
                    end_rr_reached_at_timestamp = time.perf_counter()
                    break
            else:
                raise TimeoutError(
                    f'unable to detect end RR of {expected_end_rr_sec} (+/-{allowed_dev_percent*100:.2f}%) '
                    f'in reader within {timeout_sec} seconds - received: {rr_over_history}'
                )

            update_time = end_rr_reached_at_timestamp - change_time
            assert update_time < self.HeartRateSensor.config.max_rr_change_update_time_sec, \
                (f"time to update RR values for {start_bpm}bpm to {end_bpm}bpm needed {update_time} seconds "
                 f"(expectation was below {self.HeartRateSensor.config.max_rr_change_update_time_sec} seconds)")

            time.sleep(time_to_wait_when_reached_sec)

            # TODO validate history -> should not go down and stay within the allowed range
            constant_with_start_rr = [
                rr for ts, rr in rr_over_history
                if start_time + self.HeartRateSensor.config.max_rr_change_update_time_sec < ts < change_time
            ]

            assert len(constant_with_start_rr) > 0, "received nothing after set start bpm"

            assert expected_min_start_rr <= min(constant_with_start_rr) <= expected_max_start_rr, \
                (f"detect some RR after the start bpm should be detected constantly that are not within the expected "
                 f"range of {expected_min_start_rr}-{expected_max_start_rr} sec "
                 f"({expected_start_rr_sec} +/-{allowed_dev_percent*100:.2f}%): {constant_with_start_rr}")

            assert expected_min_start_rr <= max(constant_with_start_rr) <= expected_max_start_rr, \
                (f"detect some RR after the start bpm should be detected constantly that are not within the expected "
                 f"range of {expected_min_start_rr}-{expected_max_start_rr} "
                 f"({expected_start_rr_sec} +/-{allowed_dev_percent * 100:.2f}%): {constant_with_start_rr}")

            constant_with_end_rr = [
                rr for ts, rr in rr_over_history
                if change_time + self.HeartRateSensor.config.max_rr_change_update_time_sec < ts
            ]

            assert len(constant_with_end_rr) > 0, "received nothing after set end bpm"

            assert expected_min_end_rr <= min(constant_with_end_rr) <= expected_max_end_rr, \
                (f"detect some RR after the end bpm should be detected constantly that are not within the expected "
                 f"range of {expected_min_end_rr}-{expected_max_end_rr} "
                 f"({expected_end_rr_sec} +/-{allowed_dev_percent*100:.2f}%): {constant_with_end_rr}")

            assert expected_min_end_rr <= max(constant_with_end_rr) <= expected_max_end_rr, \
                (f"detect some RR after the end bpm should be detected constantly that are not within the expected "
                 f"range of {expected_min_end_rr}-{expected_max_end_rr} "
                 f"({expected_end_rr_sec} +/-{allowed_dev_percent * 100:.2f}%): {constant_with_end_rr}")
        finally:
            self.HeartRateHost.reader.cleanup()
