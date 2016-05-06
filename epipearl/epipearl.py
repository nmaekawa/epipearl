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
from endpoints.admin import AdminWebUi

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
    # these are mostly configuration calls.
    #

    @handle_http_exceptions()
    def set_ntp(self, server, timezone):
        """set ntp server and timezone in epiphan."""

        def check_tz(tag):
            return tag.name == 'option' and \
                    tag.has_attr('selected') and \
                    tag.has_attr('value') and \
                    tag['value'] == timezone

        def check_ntp_proto(tag):
            return tag.name == 'option' and \
                    tag.has_attr('selected') and \
                    tag.has_attr('value') and \
                    tag['value'] == 'NTP'

        def check_ntp_sync(tag):
            return tag.has_attr('id') and \
                    tag['id'] == 'rdate_auto' and \
                    tag.has_attr('checked') and \
                    tag.has_attr('value') and \
                    tag['value'] == 'auto'

        def check_ntp_server(tag):
            return tag.has_attr('id') and \
                    tag['id'] == 'server' and \
                    tag.has_attr('value') and \
                    tag['value'] == server

        params = {'server': server, 'tz': timezone,
                'fn': 'date', 'rdate': 'auto', 'rdate_proto': 'NTP'}

        check_success = [
                {'emsg': 'timezone setting expected(%s)' % timezone,
                    'func': check_tz},
                {'emsg': 'protocol setting expecetd(NTP)',
                    'func': check_ntp_proto},
                {'emsg': 'expected to enable sync(auto)',
                    'func': check_ntp_sync},
                {'emsg': 'expected ntp server(%s)' % server,
                    'func': check_ntp_server}]
        try:
            response = \
                    AdminWebUi.set_date_and_time(self, params, check_success)
        except SettingConfigError as e:
            return({'status_code': 400, 'msg': e.message})
        except requests.HTTPError:
            return({'status_code': 0, 'msg': '--'.join(
                [e.msg, e.original_error.message])})
        else:
            return response








