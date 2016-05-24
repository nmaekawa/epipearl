# -*- coding: utf-8 -*-

"""
epipearl client
---------------
defines the main api client class
"""

from . import __version__

import os
import sys
import platform
import requests

from requests.auth import HTTPBasicAuth
from urlparse import urljoin

from errors import RequestsError
from errors import SettingConfigError
from endpoints.admin import Admin
from endpoints.webui_config import WebUiConfig

_default_timeout = 5



def handle_http_exceptions(callbacks=None):
    if callbacks is None:
        callbacks = {}
    def wrapper(f):
        def newfunc(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except requests.HTTPError as e:
                resp = e.response
                req = e.request
                if resp.status_code in callbacks.keys():
                    callbacks[resp.status_code](e)
                else:
                    raise
            except Exception, e:
                raise
        return newfunc
    return wrapper


def default_useragent():
    """Return a string representing the default user agent."""
    _implementation = platform.python_implementation()

    if _implementation == 'CPython':
        _implementation_version = platform.python_version()
    elif _implementation == 'PyPy':
        _implementation_version = '%s.%s.%s' % (sys.pypy_version_info.major,
                                                sys.pypy_version_info.minor,
                                                sys.pypy_version_info.micro)
        if sys.pypy_version_info.releaselevel != 'final':
            _implementation_version = ''.join([_implementation_version, sys.pypy_version_info.releaselevel])
    elif _implementation == 'Jython':
        _implementation_version = platform.python_version()  # Complete Guess
    elif _implementation == 'IronPython':
        _implementation_version = platform.python_version()  # Complete Guess
    else:
        _implementation_version = 'Unknown'

    try:
        p_system = platform.system()
        p_release = platform.release()
    except IOError:
        p_system = 'Unknown'
        p_release = 'Unknown'

    return " ".join(['%s/%s' % (__name__, __version__),
                    '%s/%s' % (_implementation, _implementation_version),
                    '%s/%s' % (p_system, p_release)])


class Epipearl(object):

    def __init__(self, base_url, user, passwd, timeout=None):
        self.url = base_url
        self.user = user
        self.passwd = passwd
        self.timeout = timeout or _default_timeout
        self.default_headers = {
                'User-Agent': default_useragent(),
                'Accept-Encoding': ', '.join(('gzip', 'deflate')),
                'Accept' : 'text/html, text/*, video/avi',
                'X-REQUESTED-AUTH': 'Basic' }


    def get(self, path, params=None, extra_headers=None):
        if params is None:
            params = {}
        if extra_headers is None:
            extra_headers = {}
        headers = self.default_headers.copy()
        headers.update(extra_headers)

        url = urljoin(self.url, path)
        auth = HTTPBasicAuth(self.user, self.passwd)
        resp = requests.get(url,
                params=params,
                auth=auth,
                headers=headers,
                timeout=self.timeout)

        resp.raise_for_status()
        return resp

    def post(self, path, data=None, extra_headers=None):
        if data is None:
            data = {}
        if extra_headers is None:
            extra_headers = {}
        headers = self.default_headers.copy()
        headers.update(extra_headers)

        url = urljoin(self.url, path)
        auth = HTTPBasicAuth(self.user, self.passwd)
        resp = requests.post(url,
                data=data,
                auth=auth,
                headers=headers,
                timeout=self.timeout)

        resp.raise_for_status()
        return resp

    def put(self, path, data={}, extra_headers={}):
        raise NotImplementedError()

    def delete(self, path, params={}, extra_headers={}):
        raise NotImplementedError()


    @handle_http_exceptions()
    def get_params(self, channel, params=None):
        if params is None:
            params = {}
        response = Admin.get_params(self, channel, params);
        r = {}
        for line in response['response_text'].splitlines():
            (key, value) = [x.strip() for x in line.split('=')]
            r[key] = value
        return r


    @handle_http_exceptions()
    def set_params(self, channel, params):
        response = Admin.set_params(self, channel, params);
        return 2 == (response['status_code']/100)


    #
    # calls done to the web ui
    # some functionality is not available via http api;
    # methods below send forms (or gets) to the web ui.
    #
    # beware that these are design to fit dce config reqs!
    #

    @handle_http_exceptions()
    def set_ntp(self, server, timezone):
        """set ntp server and timezone in epiphan.

        raises SettingConfigError if error message from webui
            or if the configs didn't update webui (didn't take)
        raises requests.RequestException|ConnectionError|Timeout
        """
        return WebUiConfig.set_ntp(
                client=self,
                server=server,
                timezone=timezone)


    @handle_http_exceptions()
    def set_touchscreen(self, screen_timeout=600):
        """ disable settings changes and recording via touchscreen.

        raises SettingConfigError if error message from webui
            or if the configs didn't update webui (didn't take)
        raises requests.RequestException|ConnectionError|Timeout
        """
        return WebUiConfig.set_touchscreen(
                client=self,
                screen_timeout=screen_timeout)


    @handle_http_exceptions
    def set_permanent_logs(self, log_enabled=True):
        """enable/disable permanent logs.

        raises SettingConfigError if error message from webui
            or if the configs didn't update webui (didn't take)
        raises requests.RequestException|ConnectionError|Timeout
        """
        return WebUiConfig.set_support_and_permanent_logs(
                client=self,
                log_enabled=log_enabled)
