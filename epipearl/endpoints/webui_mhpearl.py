# -*- coding: utf-8 -*-
"""http api and web ui calls to epiphan pearl."""

from bs4 import BeautifulSoup
import json
import logging

from epipearl.endpoints.webui_config import WebUiConfig
import epipearl.endpoints.webui_scrape as webui_scrape
from epipearl.errors import SettingConfigError


WEBUI_MH_FORM_NAME = 'mh_config'


class WebUiMhPearl(object):
    """calls to dce mh_pearl custom api.

    these are custom api calls for mh_pearl. epiphan pearl firmware
    _does not_ support them out-of-the-box

    methods below send forms (or gets) to the web ui.
    """

    @classmethod
    def set_mhpearl_settings(
            cls, client,
            device_name='',       # device name for mh admin
            device_channel='',    # vod recorder id number
            device_live_channels=[],  # list channel id numbers
            output_streams='',    # json object with live stream output urls by
                                  # resolution; ex:
                                  # {"streams": {"960x270": "rtmp://some.url"}}
            live_nonstop=True,    # 24/7 live streaming
            file_search_range_in_seconds='',    # range within which it must
                                                # locate a recording
            admin_server_url='',  # mh admin url
            admin_server_usr='',  # mh digest user
            admin_server_pwd='',  # mh digest pwd
            update_frequency_in_seconds='120',  # freq to poll for schedule
            backup_agent=False):  # if True, does not upload recording to
                                  # mh when done

        # check that output_streams is valid json
        if output_streams:
            ostreams = json.dumps(output_streams)

        # get current settings for mhpearl
        expected = cls.get_mhpearl_settings(client)

        # update with input values to be changed
        expected['DEVICE_NAME'] = device_name
        expected['DEVICE_ADDRESS'] = client.url
        expected['DEVICE_USERNAME'] = client.user
        expected['DEVICE_PASSWORD'] = client.passwd
        expected['DEVICE_CHANNEL'] = device_channel
        expected['DEVICE_LIVE_CHANNELS'] = ','.join(device_live_channels)
        expected['DEVICE_LIVE_STREAMS'] = output_streams
        expected['FILE_SEARCH_RANGE'] = file_search_range_in_seconds
        expected['ADMIN_SERVER_URL'] = admin_server_url
        expected['ADMIN_SERVER_USER'] = admin_server_usr
        expected['ADMIN_SERVER_PASSWD'] = admin_server_pwd
        expected['UPDATE_FREQUENCY'] = update_frequency_in_seconds

        if not live_nonstop:
            expected['MANAGE_LIVE'] = 'on'
        else:
            del(expected['MANAGE_LIVE'])

        if backup_agent:
            expected['BACKUP_AGENT'] = 'on'
        else:
            del(expected['BACKUP_AGENT'])

        # keep the defaults for now
        # expected['CONNECTTIMEOUT'] =,
        # expected['LOW_SPEED_TIME'] =,
        # expected['MAX_INGEST'] =,
        # expected['INGEST_DELAY'] =,
        # expected['NUMBER_OF_RETRIES'] =,

        path = '/admin/mhcfg'
        de_facto = WebUiConfig.handle_form(
                client=client,
                path=path,
                form_name=WEBUI_MH_FORM_NAME,
                params=expected)
        for key in ['DEVICE_NAME', 'DEVICE_ADDRESS','DEVICE_USERNAME',
                'DEVICE_PASSWORD', 'DEVICE_CHANNEL', 'DEVICE_LIVE_CHANNELS',
                'FILE_SEARCH_RANGE', 'ADMIN_SERVER_URL', 'ADMIN_SERVER_USER',
                'ADMIN_SERVER_PASSWD', 'UPDATE_FREQUENCY',]:
            if str(expected[key]) != str(de_facto[key]):
                msg = 'mh_config prop({}) expected({}), got({})'.format(
                        key, expected[key], de_facto[key])
                logging.getLogger(__name__).error(msg)
                raise SettingConfigError(msg)

        # check for checkbox
        if not live_nonstop:  # expected to have it ON
            if not de_facto['MANAGE_LIVE']:
                msg = 'mh_config prop(MANAGE_LIVE) expected(ON), got(OFF)'
                raise SettingConfigError(msg)
        else:  # expected to have it OFF
            if de_facto['MANAGE_LIVE']:
                msg = 'mh_config prop(MANAGE_LIVE) expected(OFF), got(ON)'
                raise SettingConfigError(msg)

        if not backup_agent:
            if de_facto['BACKUP_AGENT']:
                msg = 'mh_config prop(BACKUP_AGENT) expected(OFF), got(ON)'
                raise SettingConfigError(msg)
        else:
            if not de_facto['BACKUP_AGENT']:
                msg = 'mh_config prop(BACKUP_AGENT) expected(ON), got(OFF)'
                raise SettingConfigError(msg)

        # check for textarea (that contains a json)
        if output_streams:
            expected_ostreams = json.loads(expected['DEVICE_LIVE_STREAMS'])
            de_facto_ostreams = json.loads(de_facto['DEVICE_LIVE_STREAMS'])
            if expected_ostreams != de_facto_ostreams:
                msg = ('mh_config prop(DEVICE_LIVE_STREAMS) expected({}), '
                    'got({})').format(expected_ostreams, de_facto_ostreams)
                logging.getLogger(__name__).error(msg)
                raise SettingConfigError(msg)

        return de_facto


    @classmethod
    def get_mhpearl_settings(cls, client):
        path = '/admin/mhcfg'
        settings = WebUiConfig.handle_form(
                client=client,
                path=path,
                form_name=WEBUI_MH_FORM_NAME)

        # TODO: how to sanity check?
        return settings

# names of form fields for mh_config
#                tag_names = [
#                    'DEVICE_NAME',
#                    'DEVICE_ADDRESS',
#                    'DEVICE_USERNAME',
#                    'DEVICE_PASSWORD',
#                    'DEVICE_CHANNEL',
#                    'DEVICE_LIVE_CHANNELS',
#                    'DEVICE_LIVE_STREAMS',
#                    'MANAGE_LIVE',
#                    'FILE_SEARCH_RANGE',
#                    'ADMIN_SERVER_URL',
#                    'ADMIN_SERVER_USER',
#                    'ADMIN_SERVER_PASSWD',
#                    'UPDATE_FREQUENCY',
#                    'CONNECTTIMEOUT',
#                    'LOW_SPEED_TIME',
#                    'MAX_INGEST',
#                    'INGEST_DELAY',
#                    'NUMBER_OF_RETRIES',
#                    'BACKUP_AGENT',
#                ]
