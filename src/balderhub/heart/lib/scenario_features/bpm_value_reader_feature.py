import balder


class BpmValueReaderFeature(balder.Feature):
    """
    Base scenario-level feature class for reading BPM value remotely from the DUT
    """

    def prepare(self):
        """method that prepares the feature"""

    def read_last_bpm_value(self) -> int:
        """reads the RR-Value from the DUT once"""
        raise NotImplementedError

    def cleanup(self):
        """method to clean up the resources used by the feature"""
