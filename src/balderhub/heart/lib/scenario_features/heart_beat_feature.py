import logging
from typing import Union

import balder


logger = logging.getLogger(__name__)


class HeartBeatFeature(balder.Feature):
    """Base scenario level heart beat feature"""

    def start(self, bpm: float) -> None:
        """
        Starts the heart beat simulation

        :param bpm: the beats-per-minute that should be applied
        """
        raise NotImplementedError

    def stop(self) -> None:
        """
        Stops the heart beat simulation
        """
        raise NotImplementedError

    def get_current_active_bpm(self) -> Union[float, None]:
        """
        :return: returns the current active heart beat or None if no heart beat is active at the moment
        """
        raise NotImplementedError

    def _fixture_teardown(self, heart_beat_before: Union[float, None] = None):
        current_level = self.get_current_active_bpm()
        if heart_beat_before is not None:

            if current_level == heart_beat_before:
                logger.info(f'Heart beat before entering this fixture is equal with the current heart beat of '
                            f'{current_level} bpm -> nothing to do')
            else:
                logger.info(f'Current heart beat is {current_level} bpm but was {heart_beat_before} bpm before '
                            f'entering this fixture -> restart with {current_level} bpm')
                self.stop()
                self.start(heart_beat_before)
        else:
            if current_level:
                logger.info('No heart beat was active before entering this fixture, but it is still active now '
                            '-> stop heart beat')
                self.stop()
            else:
                logger.info('No heart beat was active before entering this fixture and is still not active '
                            '-> do nothing')

    def fixt_make_sure_heart_beat_established(self, with_bpm: float= 60, restore_entry_state: bool = True):
        """
        Fixture that makes sure that the Heart Beat is established with the given beats-per-minute value. If there is
        another beat-per-minute value established established, the method will update it to the new one and saves the
        previous applied value which can be restored within teardown code (if ``restore_entry_state`` is True).

        .. note::

            You can use this fixture directly by using:

            .. code-block:: python

                @balder.fixture(...)
                def my_fixture(...):
                    yield from feat.fixt_make_sure_heart_beat_established(...)

        :param with_bpm: the beat-per-minute that should be established
        :param restore_entry_state: True if the previous state should be reestablished in the teardown part of this
                                    fixture
        :return: the ready to use fixture generator, but without any values
        """
        heart_beat_before = self.get_current_active_bpm()
        if heart_beat_before:
            if heart_beat_before != with_bpm:
                logger.info(f'Heart beat is already active with {heart_beat_before}, which is not the required '
                            f'{with_bpm} bpm -> restart with new {with_bpm} bpm')
                self.stop()
                self.start(with_bpm)
            else:
                logger.info(f'Heart beat is already active with required {with_bpm} bpm -> do nothing')
        else:
            logger.info(f'no active heart beat detected -> start it with {with_bpm} bpm')
            self.start(with_bpm)
        yield
        if not restore_entry_state:
            return
        self._fixture_teardown(heart_beat_before=heart_beat_before)

    def fixt_make_sure_heart_beat_off(self, restore_entry_state: bool = True):
        """
        Fixture that makes sure that the Heart Beat is put off before finishing the construction part of this
        fixture.

        If `restore_entry_state` is True, the method will reestablish the state that was given before entering this
        fixture.

        .. note::

            You can use this fixture directly by using:

            .. code-block:: python

                @balder.fixture(...)
                def my_fixture(...):
                    yield from feat.fixt_make_sure_heart_beat_off(...)

        :param restore_entry_state: True if the previous state should be reestablished in the teardown part of this
                                    fixture
        :return: the ready to use fixture generator, but without any values
        """
        heart_beat_before = self.get_current_active_bpm()

        if heart_beat_before:
            logger.info(f'Heart beat with {heart_beat_before} bpm is still active -> stop it')
            heart_beat_before = self.get_current_active_bpm()
            self.stop()
        else:
            logger.info('No heart beat is active at the moment - do nothing')
        yield
        if not restore_entry_state:
            return
        self._fixture_teardown(heart_beat_before=heart_beat_before)
