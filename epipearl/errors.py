# -*- coding: utf-8 -*-
"""exception for epipearl cadash."""

class Error(Exception):
    """base class to all exceptions raised by this module."""


class SettingConfigError(Error):
    """error in settings configs, usually benign warnings."""


class IndiscernibleResponseFromWebUiError(Error):
    """unexpected result from epiphan device; call failed"""


class RequestsError(Error):
    """error during connection or 500."""
