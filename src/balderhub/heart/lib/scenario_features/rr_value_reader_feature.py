import balder


class RRValueReaderFeature(balder.Feature):
    """
    Base scenario-level feature class for reading the RR-Value remotely from the DUT
    """

    def prepare(self):
        """method that prepares the feature"""

    def read_last_rr_value_in_sec(self):
        """reads the RR-Value from the DUT once"""
        raise NotImplementedError

    def cleanup(self):
        """method to clean up the resources used by the feature"""
