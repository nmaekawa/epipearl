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
from endpoints.admin_webui import AdminWebUi

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
                    AdminWebUi.configuration(
                            client=self,
                            path='admin/timesynccfg',
                            params=params,
                            check_success=check_success)

        except SettingConfigError as e:
            return({'status_code': 400, 'msg': e.message})
        except requests.HTTPError as e:
            return({'status_code': 0, 'msg': '--'.join(
                [e.msg, e.original_error.message])})
        else:
            return response

    @handle_http_exceptions()
    def set_touchscreen(self, screen_timeout=600):
        """ disable settings changes and recording via touchscreen."""

        def check_display_enabled(tag):
            return tag.has_attr('id') and \
                    tag['id'] == 'epiScreenEnabled' and \
                    tag.has_attr('checked')

        def check_preview_enabled(tag):
            return tag.har_attr('id') and \
                    tag['id'] == 'showVideo' and \
                    tag.has_attr('checked')

        def check_status_displayed(tag):
            return tag.has_attr('id') and \
                    tag['id'] == 'showInfo' and \
                    tag.har_attr('checked')

        def check_settings_disabled(tag):
            return tag.has_attr('id') and \
                    tag['id'] == 'changeSettings' and \
                    not tag.has_attr('checked')

        def check_recording_disabled(tag):
            return tag.has_attr('id') and \
                    tag['id'] == 'recordControl' and \
                    not tag.has_attr('checked')

        def check_screen_timeout(tag):
            return tag.has_attr('id') and \
                    tag['id'] == 'epiScreenTimeout' and \
                    tag.has_attr('value') and \
                    int(tag['value']) == screen_timeout

        params = {'pdf_form_id': 'fn_episcreen',
                'epiScreenEnabled': 'on',
                'epiScreenTimeout': screen_timeout,
                'showVideo': 'on',
                'showInfo': 'on'}

        check_success = [
                {'emsg': 'epiScreenEnabled ON expected',
                    'func': check_display_enabled},
                {'emsg': 'epiScreenTimeout expected(%s)' % screen_timeout,
                    'func': check_screen_timeout},
                {'emsg': 'showPreview ON expected',
                    'func': check_preview_enabled},
                {'emsg': 'showSystemStatus ON expected',
                    'func': check_status_displayed},
                {'emsg': 'changeSettings OFF expected',
                    'func': check_settings_disabled},
                {'emsg': 'recordControl OFF expected',
                    'func': check_recording_disabled}]
        try:
            response = \
                AdminWebUi.configuration(
                        client=self,
                        path='admin/touchscreencfg',
                        params=params,
                        check_success=check_success)

        except SettingConfigError as e:
            return ({'status_code': 400, 'msg': e.message})
        except requests.HTTPError as e:
            return({'status_code': 0, 'msg': '--'.join(
                [e.msg, e.original_error.message])})
        else:
            return response


    @handle_http_exceptions
    def set_remote_support_and_permanent_logs(self, log_enabled=True):
        """enable/disable permanent logs."""
        _default_server = 'epiphany.epiphan.com'
        _default_port = '30'

        def check_remote_support_enabled(tag):
            return tag.has_attr('id') and \
                    tag['id'] == 'enabledssh' and \
                    tag.has_attr('checked')

        def check_server_connection_enabled(tag):
            return tag.has_attr('id') and \
                    tag['id'] == 'tunnel' and \
                    tag.has_attr('checked')

        def check_server_address(tag):
            return tag.has_attr('id') and \
                    tag['id'] == 'tunnelsrv' and \
                    tag.has_attr('value') and \
                    tag['value'] == _default_server

        def check_server_port(tag):
            return tag.has_attr('id') and \
                    tag['id'] == 'tunnelport' and \
                    tag.has_attr('value') and \
                    tag['value'] == _default_port

        def check_permanent_logs_enabled(tag):
            return tag.has_attr('id') and \
                    tag['id'] == 'permanent_logs' and \
                    tag.has_attr('checked')
        def check_permanent_logs_disabled(tag):
            return tag.has_attr('id') and \
                    tag['id'] == 'permanent_logs' and \
                    not tag.has_attr('checked')

        params = {'enablessh': 'on',
                'tunnel': 'on',
                'tunnelsrv': _default_server,
                'tunnelport': _default_port}

        check_success = [
                {'emsg': 'remote_support ON expected',
                    'func': check_remote_support_enabled},
                {'emsg': 'server_connection ON expected',
                    'func': check_server_connection_enabled},
                {'emsg': 'server_address expected(%s)' % _default_server,
                    'func': check_server_address},
                {'emsg': 'server_port expected(%s)' % _default_port,
                    'func': check_server_port}]

        if log_enabled:
            params['permanent_logs']= 'on'
            check_success.append(
                {'emsg': 'permanent logs expected to be ON',
                    'func': check_permanent_logs_enabled})
        else:
            check_success.append(
                {'emsg': 'permanent logs expected to be OFF',
                    'func': check_permanent_logs_disabled})
        try:
            response = \
                    AdminWebUi.configuration(
                            client=self,
                            path='admin/maintenancetfg',
                            params=params,
                            check_success=check_success)
        except SettingConfigError as e:
            return ({'status_code': 400, 'msg': e.message})
        except requests.HTTPError as e:
            return ({'status_code': 0, 'msg': '--'.join(
                [e.msg, e.original_error.message])})
        else:
            return response
