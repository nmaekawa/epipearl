# -*- coding: utf-8 -*-

"""
epipearl client
---------------
defines the main api client class
"""

from . import __version__

import logging
import os
import sys
import platform
import requests

from requests.auth import HTTPBasicAuth
from urlparse import urljoin

from endpoints.admin import Admin
from endpoints.admin import AdminAjax
from endpoints.webui_channel import WebUiChannel
from endpoints.webui_config import WebUiConfig
from endpoints.webui_mhpearl import WebUiMhPearl
from errors import IndiscernibleResponseFromWebUiError
from errors import SettingConfigError
from errors import RequestsError

_default_timeout = 5


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


    def get_params(self, channel, params=None):
        if params is None:
            params = {}
        response = Admin.get_params(self, channel, params);
        r = {}
        for line in response['response_text'].splitlines():
            (key, value) = [x.strip() for x in line.split('=')]
            r[key] = value
        return r


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

    def set_ntp(self, server, timezone):
        """sets ntp server and timezone in epiphan.

        raises SettingConfigError if error message from webui
            or if the configs didn't update webui (didn't take)
        raises requests.RequestException|ConnectionError|Timeout
        """
        return WebUiConfig.set_ntp(
                client=self,
                server=server,
                timezone=timezone)


    def set_touchscreen(self, screen_timeout=600):
        """ disables settings changes and recording via touchscreen.

        raises SettingConfigError if error message from webui
            or if the configs didn't update webui (didn't take)
        raises requests.RequestException|ConnectionError|Timeout
        """
        return WebUiConfig.set_touchscreen(
                client=self,
                screen_timeout=screen_timeout)


    def set_permanent_logs(self, log_enabled=True):
        """enables/disables permanent logs.

        raises SettingConfigError if error message from webui
            or if the configs didn't update webui (didn't take)
        raises requests.RequestException|ConnectionError|Timeout
        """
        return WebUiConfig.set_support_and_permanent_logs(
                client=self,
                log_enabled=log_enabled)


    def create_channel(self, channel_name, layout, layout_id='1'):
        """creates new channel with given channel_name and layout.

        raises IndiscernibleResponseFromWebUiError or Requests.Error
        or returns True when successfull
        """
        logger = logging.getLogger(__name__)
        channel_id = None
        try:
            channel_id = WebUiChannel.create_channel(client=self)
        except Exception as e:
            msg = 'failed to create channel(%s) - %s' % \
                    (channel_name, e.message)
            logger.error(msg)
            raise RequestsError(msg)
        try:
            WebUiChannel.rename_channel(client=self,
                channel_id=channel_id, channel_name=channel_name)
        except Exception as e:
            msg = 'failed to rename channel(%s)(%s) - %s' % \
                    (channel_id, channel_name, e.message)
            logger.error(msg)
            raise RequestsError(msg)
        try:
            WebUiChannel.set_channel_layout(client=self,
                    channel_id=channel_id,
                    layout=layout,
                    layout_id=layout_id)
        except Exception as e:
            msg = 'failed to set layout to channel(%s)(%s) - %s' \
                    % (channel_id, channel_name, e.message)
            logger.error(msg)
            raise RequestsError(msg)

        return True


    def set_channel_rtmp(self, channel_id,
            rtmp_url, rtmp_stream, rtmp_usr, rtmp_pwd):
        """configs rtmp-push for live streaming in given channel.

        raises IndiscernibleResponseFromWebUiError or Requests.Error
        or returns True when successfull
        """
        return WebUiChannel.set_channel_rtmp(client=self,
                channel_id=channel_id,
                rtmp_url=rtpm_url,
                rtmp_stream=rtmp_stream,
                rtpm_usr=rtmp_usr,
                rtmp_pwd=rtpm_pwd)


    def create_recorder(self, recorder_name, channel_list):
        """creates new recorder with given channel_list.

        """
        recorder_id = None
        try:
            recorder_id = WebUiChannel.create_recorder(client=self)
        except Exception as e:
            msg = 'failed to create recorder(%s) - %s' % \
                    (recorder_name, e.message)
            logging.getLogger(__name__).error(msg)
            raise RequestsError(msg)
        try:
            WebUiChannel.rename_recorder(client=self,
                    recorder_id=recorder_id,
                    recorder_name=recorder_name)
        except Exception as e:
            msg = 'failed to rename recorder(%s)(%s) - %s' % \
                    (recorder_id, recorder_name, e.message)
            logging.getLogger(__name__).error(msg)
            raise RequestsError(msg)
        try:
            WebUiChannel.set_recorder_channels(client=self,
                    recorder_id=recorder_id,
                    channel_list=channel_list)
        except Exception as e:
            msg = 'failed to set channels for recorder(%s)(%s) - %s' % \
                    (recorder_id, recorder_name, e.message)
            logging.getLogger(__name__).error(msg)
            raise RequestsError(msg)

        return True


    def set_recording_settings(self, recorder_id,
            recording_timelimit_in_minutes=360,        # 6h
            recording_sizelimit_in_kilobytes=64000000, # 64G
            output_format='avi', # or mov, mp4, ts(mpeg-ts)
            user_prefix='',      # prefix for recording file
            afu_enabled='on',    # this means auto-upload disabled!
            upnp_enabled=None):
        """configs settings for give recorder_id.

        """
        return WebUiChannel.set_recorder_settings(client=self,
                recorder_id=record_id,
                recording_timelimit_in_minutes=recording_timelimit_in_minutes,
                recording_sizelimit_in_kilobytes=recording_sizelimit_in_kilobytes,
                output_format=output_format,
                user_prefix=user_prefix,
                afu_enabled=afu_enabled,
                upnp_enabled=upnp_enabled)


    def delete_recorder(self, recorder_id):
        """deletes given recorder_id.
        """
        return WebUiChannel.delete_recorder(client=self,
                recorder_id=recorder_id)


    def delete_channel(self, channel_id):
        """deletes given channel_id.
        """
        return WebUiChannel.delete_recorder(client=self,
                channel_id=channel_id)


    def set_mhpearl_settings(self,
            device_name='',       # device name for mh admin
            device_channel='',    # vod recorder id number
            file_search_range_in_seconds='', # range within to locate a recording
            admin_server_url='',  # mh admin url
            admin_server_usr='',  # mh digest user
            admin_server_pwd='',  # mh digest pwd
            update_frequency_in_seconds='120',  # frequency to poll for schedule
            backup_agent=False):  # if True, does not upload recording to mh when done
        """configures mhpearl.

        this is a custom api call and it's not available in out-of-the-box firmware
        for epiphan-pearl.

        raises SettingConfigError if error message from webui
            or if the configs didn't update webui (didn't take)
        raises requests.RequestException|ConnectionError|Timeout
        """
        return WebUiMhPearl.set_mhpearl_settings(
                client=self,
                device_name=device_name,
                device_channel=device_channel,
                file_search_range_in_seconds=file_search_range_in_seconds,
                admin_server_url=admin_server_url,
                admin_server_usr=admin_server_usr,
                admin_server_pwd=admin_server_pwd,
                update_frequency_in_seconds=update_frequency_in_seconds,
                backup_agent=backup_agent)


    def delete_channel_or_recorder_by_name(self, channel_name):
        """deletes all channels or recorders by given channel name.

        ignores case where there's no id for a matched channel name,
        or when there are no channels in the returned json and
        returns success.
        """
        # query device for configured channels
        try:
            r_sysinfo = AdminAjax.get_sysinfo(client=self)
        except Exception as e:
            msg = 'failed to GET sysinfo for device(%s) - %s' % \
                    (self.url, e.message)
            logging.getLogger(__name__).error(msg)
            raise RequestsError(msg)

        # query returned by was unsuccessful
        if r_sysinfo['status_code'] != 200:
            msg = 'error in GET json_sysinfo from device(%s)' % self.url
            msg += ' - status_code(%s)' % r_sysinfo['status_code']
            logging.getLogger(__name__).error(msg)
            raise RequestsError(msg)

        # query returned json object!
        channel_id = []
        sysinfo = r_sysinfo['response_json']

        if 'channels' in sysinfo:
            for c in sysinfo['channels']:
                if 'name' in c and 'id' in c:      # skip if not enough info
                    if c['name'] == channel_name:  # but it's not an error...
                        channel_id.append(c['id'])

        if len(channel_id) == 0:
            return True  # most definitely no channels with channel-name

        for i in channel_id:
            try:
                 WebUiChannel.delete_channel(client=self, channel_id=i)
            except Exception as e:
                msg = 'failed to delete channel(%s)(%s) from device(%s) - %s' % \
                        (channel_id, channel_name, self.url, e.message)
                logging.getLogger(__name__).error(msg)
                raise RequestsError(msg)

        return True


