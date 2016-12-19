# -*- coding: utf-8 -*-
"""http api and web ui calls to epiphan pearl."""

from bs4 import BeautifulSoup

from epipearl.endpoints.webui_config import WebUiConfig


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

        # get current settings for mhpearl
        current = cls.get_mhpearl_settings(client)

        # update with input values to be changed
        current['DEVICE_NAME'] = device_name
        current['DEVICE_ADDRESS'] = client.url
        current['DEVICE_USERNAME'] = client.user
        current['DEVICE_PASSWORD'] = client.passwd
        current['DEVICE_CHANNEL'] = device_channel
        current['DEVICE_LIVE_CHANNELS'] = ','.join(device_live_channels)
        current['DEVICE_LIVE_STREAMS'] = output_streams
        current['FILE_SEARCH_RANGE'] = file_search_range_in_seconds
        current['ADMIN_SERVER_URL'] = admin_server_url
        current['ADMIN_SERVER_USER'] = admin_server_usr
        current['ADMIN_SERVER_PASSWD'] = admin_server_pwd
        current['UPDATE_FREQUENCY'] = update_frequency_in_seconds




        # keep the defaults for now
        # current['CONNECTTIMEOUT'] =,
        # current['LOW_SPEED_TIME'] =,
        # current['MAX_INGEST'] =,
        # current['INGEST_DELAY'] =,
        # current['NUMBER_OF_RETRIES'] =,

        check_success = [
                {
                    'emsg': 'device_name expected({})'.format(device_name),
                    'func': WebUiConfig.check_input_id_value(
                        tag_id='ca_name', value=device_name),
                },
                {
                    'emsg': 'device_username expected({})'.format(client.user),
                    'func': WebUiConfig.check_input_id_value(
                        tag_id='ca_user', value=client.user),
                },
                {
                    'emsg': 'not the device_password expected',
                    'func': WebUiConfig.check_input_id_value(
                        tag_id='ca_pass', value=client.passwd),
                },
                {
                    'emsg': 'device_channel expected({})'.format(device_channel),
                    'func': WebUiConfig.check_input_id_value(
                        tag_id='ca_chan', value=device_channel),
                },
                {
                    'emsg': 'live channels expected({})'.format(
                        ','.join(device_live_channels)),
                    'func': WebUiConfig.check_input_id_value(
                        tag_id='ca_live_chan',
                        value=','.join(device_live_channels)),
                },
                {
                    'emsg': 'output live streams expected: {}'.format(
                        output_streams),
                    'func': WebUiConfig.check_textarea_id_value(
                        tag_id='ca_live_stream', value=output_streams),
                },
                {
                    'emsg': 'file_search_range expected({})'.format(
                        file_search_range_in_seconds),
                    'func': WebUiConfig.check_input_id_value(
                        tag_id='ca_range',
                        value=str(file_search_range_in_seconds)),
                },
                {
                    'emsg': 'admin_server_url expected({})'.format(
                        admin_server_url),
                    'func': WebUiConfig.check_input_id_value(
                        tag_id='mh_host', value=admin_server_url),
                },
                {
                    'emsg': 'admin_server_user expected({})'.format(
                        admin_server_usr),
                    'func': WebUiConfig.check_input_id_value(
                        tag_id='mh_user', value=admin_server_usr),
                },
                {
                    'emsg': 'not the admin_server_passwd expected',
                    'func': WebUiConfig.check_input_id_value(
                        tag_id='mh_pass', value=admin_server_pwd),
                },
                {
                    'emsg': 'update_frequency expected({})'.format(
                        update_frequency_in_seconds),
                    'func': WebUiConfig.check_input_id_value(
                        tag_id='mh_freq',
                        value=str(update_frequency_in_seconds)),
                },
                {
                    'emsg': 'connecttimeout expected({})'.format(
                        current['CONNECTTIMEOUT']),
                    'func': WebUiConfig.check_input_id_value(
                        tag_id='mh_connecttimeout',
                        value=str(current['CONNECTTIMEOUT'])),
                },
                {
                    'emsg': 'low_speed_time expected({})'.format(
                        current['LOW_SPEED_TIME']),
                    'func': WebUiConfig.check_input_id_value(
                        tag_id='mh_low_speed',
                        value=str(current['LOW_SPEED_TIME'])),
                },
                {
                    'emsg': 'max_ingest expected({})'.format(
                        current['MAX_INGEST']),
                    'func': WebUiConfig.check_input_name_value(
                        tag_name='MAX_INGEST',
                        value=str(current['MAX_INGEST'])),
                },
                {
                    'emsg': 'ingest_delay expected({})'.format(
                        current['INGEST_DELAY']),
                    'func': WebUiConfig.check_input_name_value(
                        tag_name='INGEST_DELAY',
                        value=str(current['INGEST_DELAY'])),
                },
                {
                    'emsg': 'number_of_retries expected({})'.format(
                        current['NUMBER_OF_RETRIES']),
                    'func': WebUiConfig.check_input_name_value(
                        tag_name='NUMBER_OF_RETRIES',
                        value=str(current['NUMBER_OF_RETRIES'])),
                },
            ]

        if not live_nonstop:
            current['MANAGE_LIVE'] = 'on'
            check_success.append({
                'emsg': 'live_nonstop expected("ON")',
                'func': WebUiConfig.check_singlevalue_checkbox(
                    tag_id='manage_live')})
        else:
            check_success.append({
                'emsg': 'live_nonstop expected("OFF")',
                'func': WebUiConfig.
                        check_singlevalue_checkbox_disabled(
                            tag_id='manage_live')})

        if backup_agent:
            current['BACKUP_AGENT'] = 'on'
            check_success.append({
                'emsg': 'backup_agent expected("ON")',
                'func': WebUiConfig.check_singlevalue_checkbox(
                    tag_id='mh_backup')})
        else:
            check_success.append({
                'emsg': 'backup_agent expected("OFF")',
                'func': WebUiConfig.
                        check_singlevalue_checkbox_disabled(
                            tag_id='mh_backup')})

        path = '/admin/mhcfg'
        return WebUiConfig.configuration(
                client=client,
                params=current,
                path=path,
                check_success=check_success)


    @classmethod
    def get_mhpearl_settings(cls, client):
        path = '/admin/mhcfg'
        resp = client.get(path)
        soup = BeautifulSoup(resp.text, 'html.parser')
        return WebUiConfig.scrape_form_values(
                soup=soup,
                tag_names = [
                    'DEVICE_NAME',
                    'DEVICE_ADDRESS',
                    'DEVICE_USERNAME',
                    'DEVICE_PASSWORD',
                    'DEVICE_CHANNEL',
                    'DEVICE_LIVE_CHANNELS',
                    'DEVICE_LIVE_STREAMS',
                    'MANAGE_LIVE',
                    'FILE_SEARCH_RANGE',
                    'ADMIN_SERVER_URL',
                    'ADMIN_SERVER_USER',
                    'ADMIN_SERVER_PASSWD',
                    'UPDATE_FREQUENCY',
                    'CONNECTTIMEOUT',
                    'LOW_SPEED_TIME',
                    'MAX_INGEST',
                    'INGEST_DELAY',
                    'NUMBER_OF_RETRIES',
                    'BACKUP_AGENT',
                ]
        )
