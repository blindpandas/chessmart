from abc import ABC, abstractmethod


class AbstractAccount(ABC):
    """An abstract class for Account API Endpoint"""

    @abstractmethod
    def get_my_profile(self):
        """
        Public information about the logged in user.
        """
        pass

    @abstractmethod
    def get_my_email_address(self):
        """
        Read the email address of the logged in user.
        """
        pass

    @abstractmethod
    def get_my_preferences(self):
        """
        Read the preferences of the logged in user.
        """
        pass

    @abstractmethod
    def get_my_kid_mode_status(self):
        """
        Read the kid mode status of the logged in user.
        """
        pass

    @abstractmethod
    def set_my_kid_mode_status(self, *, turned_on: bool):
        """
        Set the kid mode status of the logged in user.

        Parameters
        ----------
        turned_on: bool, required
            The indicator to turn on or turn off the kid mode.
        """
        pass
