from typing import Union
import balder


class RRValueReaderFeature(balder.Feature):
    """
    Base scenario-level feature class for reading the RR-Value remotely from the DUT
    """

    def prepare(self):
        """method that prepares the feature"""

    def read_last_rr_value_in_sec(self) -> Union[float, None]:
        """
        reads the RR-Value from the DUT once

        :return: the rr-value time in seconds or None if measurement was not possible this time
        """
        raise NotImplementedError

    def wait_for_next_rr_value_in_sec(self) -> Union[float, None]:
        """
        Waits until the next RR-Value is available

        :return: the rr-value time in seconds or None if measurement was not possible this time
        """
        raise NotImplementedError

    def cleanup(self):
        """method to clean up the resources used by the feature"""
