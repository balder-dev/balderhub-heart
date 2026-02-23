from balderhub.heart.lib.scenario_features.base_test_criteria_config import BaseTestCriteriaConfig


class StrapTestCriteriaConfig(BaseTestCriteriaConfig):
    """
    Special Test Criteria configuration for tests with chest straps
    """

    @property
    def time_to_sleep_after_no_signal(self) -> float:
        """
        :return: maximum time device needs to go to sleep if no heart beat signal is active
        """
        return 10

    @property
    def time_to_sleep_after_skin_contact_loss(self) -> float:
        """
        :return: maximum time device needs to go to sleep if no connection is established
        """
        return 10

    @property
    def timeout_awakening_sec(self) -> float:
        """
        :return: maximum time device needs to awake
        """
        return 3.0
