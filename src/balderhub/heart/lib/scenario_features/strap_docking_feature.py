import logging
import balder

logger = logging.getLogger(__name__)


class StrapDockingFeature(balder.Feature):
    """
    Feature providing binding to dock and undock a heart beat sensor device at the skin. It is pretty common, that chest
    staps can detect skin contact and stops working as soon as the skin contact is lost. This feature provides bindings
    for that.
    """

    def put_on(self) -> None:
        """
        Puts strap on
        """
        raise NotImplementedError()

    def put_off(self) -> None:
        """
        Puts strap off
        """
        raise NotImplementedError()

    def is_attached(self) -> bool:
        """
        :return: returns True if the stap is attached, otherwise False
        """
        raise NotImplementedError()

    def _fixture_teardown(self, state_before: bool):
        current_state = self.is_attached()
        if state_before:
            if current_state:
                logger.info('strap was attached before entering this fixture and is still attached -> do nothing')
            else:
                logger.info('strap was attached before entering this fixture but it is not attached anymore '
                            '-> put it on again')
                self.put_on()
        else:
            if current_state:
                logger.info('strap was not attached before entering this fixture but is attached now '
                            '-> put it off again')
                self.put_off()
            else:
                logger.info('strap was not attached before entering this fixture and is also not attached now '
                            '-> do nothing')

    def fixt_make_sure_to_be_attached(self, restore_entry_state: bool = True):
        """
        This is a fixture that ensures that the strap is attached before finishing the construction part of this
        fixture.

        If ``restore_entry_state`` is True, it will restore the state that was applied before entering this fixture in
        teardown part.

        .. note::
            You can directly use this fixture within balder like:

            .. code-block:: python

                @balder.fixture(...)
                def my_fixture(...):
                    yield from feat.fixt_make_sure_to_be_attached(...)

        :param restore_entry_state: if Ture, the fixture will restore the state of the strap like it was before
                                    entering this fixture within the teardown code
        :return: the generator object to use directly as balder fixture
        """
        state_before = self.is_attached()
        if state_before:
            logger.info('Strap is still attached -> do not change anything')
        else:
            logger.info('Strap is not attached -> put it on now')
            self.put_on()
        yield
        if not restore_entry_state:
            return
        self._fixture_teardown(state_before)

    def fixt_make_sure_to_be_not_attached(self, restore_entry_state: bool = True):
        """
        This is a fixture that ensures that the strap is put off before finishing the construction part of this
        fixture.

        If ``restore_entry_state`` is True, it will restore the state that was applied before entering this fixture in
        teardown part.

        .. note::
            You can directly use this fixture within balder like:

            .. code-block:: python

                @balder.fixture(...)
                def my_fixture(...):
                    yield from feat.fixt_make_sure_to_be_not_attached(...)

        :param restore_entry_state: if Ture, the fixture will restore the state of the strap like it was before
                                    entering this fixture within the teardown code
        :return: the generator object to use directly as balder fixture
        """
        state_before = self.is_attached()
        if state_before:
            logger.info('Strap is still attached -> put it off now')
            self.put_off()
        else:
            logger.info('Strap is not attached -> do not change anything')
        yield
        if not restore_entry_state:
            return
        self._fixture_teardown(state_before)
