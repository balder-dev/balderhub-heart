import balder
from balder.connections import DCPowerConnection

from balderhub.battery.lib.scenario_features import RemovableBatterySimFeature
import balderhub.heart.lib.scenario_features

from balderhub.heart.lib.scenario_features.strap_test_criteria_config import StrapTestCriteriaConfig


class BaseScenarioEnv(balder.Scenario):
    """Base scenario class for validating heart rate sensor strap devices"""

    class HeartRateGiver(balder.Device):
        """simulation device that initiate the hear rate"""
        heart = balderhub.heart.lib.scenario_features.HeartBeatFeature()

    @balder.connect(HeartRateGiver, over_connection=balder.Connection)  # pylint: disable=undefined-variable
    class HeartRateSensor(balder.Device):
        """device detecting the row heart rate"""
        config = StrapTestCriteriaConfig()
        strap = balderhub.heart.lib.scenario_features.StrapDockingFeature()

    @balder.connect(HeartRateSensor, over_connection=DCPowerConnection)  # pylint: disable=undefined-variable
    class BatterySim(balder.Device):
        """device simulating the battery"""
        sim = RemovableBatterySimFeature() # TODO use different one for Non-Removable to

    @balder.connect(HeartRateSensor, over_connection=balder.Connection)  # pylint: disable=undefined-variable
    class HeartRateHost(balder.Device):
        """device receiving the heart rate data"""
