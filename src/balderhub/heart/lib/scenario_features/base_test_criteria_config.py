from typing import NamedTuple

import balder


class BaseTestCriteriaConfig(balder.Feature):
    """base test criteria configuration for beat-per-minute sensor devices in general"""

    class UpdateTimeTestConfig(NamedTuple):
        """configuration tupe for :meth:`BaseTestCriteriaConfig.test_update_time_for`"""
        start_bpm: int
        end_bpm: int
        max_update_time_sec: float

    @property
    def max_bpm_change_update_time_sec(self):
        """
        :return: the maximum time the bpm update should need within the whole system
        """
        return 10

    @property
    def max_rr_change_update_time_sec(self):
        """
        :return: the maximum time the RR-Value update should need
        """
        return 1

    @property
    def allowed_plusminus_deviation_percent(self):
        """
        :return: allowed deviation in percent (0..1) the BPM and the RR-Value can be different to the expected value
        """
        return 0.05

    @property
    def test_noise_with_snr_of(self):
        """
        :return: list of test parametrization runs that should be done with noise (None is no Noise and all values are
                 SNR in dB)
        """
        return [None]

    @property
    def test_accuracy_of_bpms_for(self) -> list[int]:
        """
        :return: list of test parametrization runs to do with the given BPM value
        """
        return [40, 50, 70, 120, 220]

    @property
    def test_update_time_for(self) -> list[UpdateTimeTestConfig]:
        """
        :return: list of test parametrization runs to do Update time validation for specific start and end bpm values
        """
        return [
            self.UpdateTimeTestConfig(50, 70, 10),
            self.UpdateTimeTestConfig(70, 50, 10),
            self.UpdateTimeTestConfig(120, 70, 10),
            self.UpdateTimeTestConfig(220, 70, 10)
        ]
