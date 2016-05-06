# -*- coding: utf-8 -*-
"""exception for epipearl cadash."""

class Error(Exception):
    """base class to all exceptions raised by this module."""


class SettingConfigError(Error):
    """error in settings configs, usually benign warnings."""


class RequestsError(Error):
    """unexpected error from requests call."""
    def __init__(self, message, original_error):
        super(RequestError, self).__init__(self,message)
        self.original_error = original_error

