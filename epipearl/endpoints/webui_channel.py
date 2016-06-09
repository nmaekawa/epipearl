# -*- coding: utf-8 -*-
"""http api and web ui calls to epiphan pearl."""

from bs4 import BeautifulSoup
import json
import logging
import requests
import re

from epipearl.errors import IndiscernibleResponseFromWebUiError
from epipearl.errors import RequestsError
from epipearl.errors import SettingConfigError
from epipearl.endpoints.webui_config import WebUiConfig


class WebUiChannel(object):
    """calls to epiphan pearl web ui.

    these are not non-documented calls, so can break if epiphan
    changes its webui interface. and beware that these are design
    to fit dce config reqs!

    use at your own peril!!!!

    methods below send forms (or gets) to the web ui.
    """

    @classmethod
    def create_channel_or_recorder(cls, client, create_channel=True):
        """returns channel_id or recorder_id just created or exception."""
        path = '/admin/add_channel.cgi' if create_channel \
                else '/admin/add_recorder.cgi'
        try:
            r = client.get(path=path)
        except (requests.HTTPError,
                requests.RequestException,
                requests.ConnectionError,
                requests.Timeout) as e:
            msg = 'failed to call %s/%s - %s' % (client.url, path, e.message)
            logging.getLogger(__name__).error(msg)
            raise RequestsError(msg)

        else:
            # requests.get will follow the redirect and return 200
            # but keep in response.history the 302 that we want
            msg = 'failed call to %s/%s ' % (client.url, path)
            logger = logging.getLogger(__name__)

            if r.status_code == 200:
                if not r.history: # status 200 is bad in this case
                    msg += '- expect response status 302, but got (%s)' % \
                            r.status_code
                    logger.error(msg)
                    raise IndiscernibleResponseFromWebUiError(msg)

                if r.history[0].status_code != 302:
                    msg += '- expect response STATUS 302, but got (%s)' \
                            % r.history[0].status_code
                    logger.error(msg)
                    raise IndiscernibleResponseFromWebUiError(msg)

                if 'location' in r.history[0].headers: # this is actually success
                    pattern = r'/admin/channel(\d+)' if create_channel \
                            else r'/admin/recorder(\d+)'
                    p = re.findall(pattern, r.history[0].headers['location'])
                    if len(p) == 1:
                        return p[0]  # SUCCESS!
                    else:
                        msg += '- cannot parse channel created from location '
                        msg += 'header(%s)' % r.history[0].headers['location']
                        logger.error(msg)
                        raise IndiscernibleResponseFromWebUiError(msg)

                else: # 302, no header location found
                    msg += ' - missing header location for response status 302'
                    logger.error(msg)
                    raise IndiscernibleResponseFromWebUiError(msg)

            else:
                if r.status_code == 302:
                    # this means that the location header is not
                    # present, otherwise requests.get would follow
                    # the redirect and return 200
                    msg += '- location header missing.'
                else: # status code not expected (!= 302)
                    msg += ' - expect response status 302, but GOT (%s)' % r.status_code
                logger.error(msg)
                raise IndiscernibleResponseFromWebUiError(msg)


    @classmethod
    def create_channel(cls, client):
        """returns channel_id just created or exception."""
        return cls.create_channel_or_recorder(client)


    @classmethod
    def rename_channel(cls, client, channel_id, channel_name):
        """returns channel_name when success, or raises exception."""
        path = '/admin/ajax/rename_channel.cgi'
        try:
            r = client.post(path=path,
                    data={'value': channel_name,
                        'id': 'channelname', 'channel': channel_id})
        except (requests.HTTPError,
                requests.RequestException,
                requests.ConnectionError,
                requests.Timeout) as e:
            msg = 'failed to call %s/%s - %s' % (client.url, path, e.message)
            logging.getLogger(__name__).error(msg)
            raise RequestsError(msg)
        else:
            if r.status_code == 200:  # all went well
                return channel_name

            msg = 'error from call %s/%s - response status(%s)' % \
                    (client.url, path, r.status_code)
            logging.getLogger(__name__).error(msg)
            raise IndiscernibleResponseFromWebUiError(msg)


    @classmethod
    def set_channel_layout(cls, client, channel_id, layout, layout_id='1'):
        """returns the json layout set or raises exception."""
        path = '/admin/channel%s/layouts/%s' % (channel_id, layout_id)
        try:
            r = client.post(path=path, data=json.dumps(layout))
        except (requests.HTTPError,
                requests.RequestException,
                requests.ConnectionError,
                requests.Timeout) as e:
            msg = 'failed to call %s/%s - %s' % (client.url, path, e.message)
            logging.getLogger(__name__).error(msg)
            raise RequestsError(msg)
        else:
            if r.status_code == 200:
                return r.text

            msg = 'error from call %s/%s - response status(%s)' % \
                    (client.url, path, r.status_code)
            logging.getLogger(__name__).error(msg)
            raise IndiscernibleResponseFromWebUiError(msg)

    @classmethod
    def set_channel_rtmp(cls, client, channel_id,
            rtmp_url, rtmp_stream, rtmp_usr, rtmp_pwd):
        """returns true or raises exception."""

        params = {'rtmp_url': rtmp_url,
                'rtmp_stream': rtmp_stream,
                'rtmp_username': rtmp_usr,
                'rtmp_password': rtmp_pwd}

        path = '/admin/channel%s/streamsetup' % channel_id

        check_success = [
                {'emsg': 'rtmp_usr expected(%s)' % rtmp_usr,
                    'func': WebUiConfig.check_input_id_value_funcfactory(
                        tag_id='rtmp_username', value=rtmp_usr)},
                {'emsg': 'rtmp_url expected(%s)' % rtmp_url,
                    'func': WebUiConfig.check_input_id_value_funcfactory(
                        tag_id='rtmp_url', value=rtmp_url)},
                {'emsg': 'rtmp_stream expected(%s)' % rtmp_stream,
                    'func': WebUiConfig.check_input_id_value_funcfactory(
                        tag_id='rtmp_stream', value=rtmp_stream)},
                {'emsg': 'not the rtmp_pwd expected',
                    'func': WebUiConfig.check_input_id_value_funcfactory(
                        tag_id='rtmp_password', value=rtmp_pwd)}]

        return WebUiConfig.configuration(
                client=client,
                params=params,
                path=path,
                check_success=check_success)


    @classmethod
    def delete_channel(cls, client, channel_id):
        """returns true or raises exception.

        param: channel_id: number id of channel to be deleted
            note that this returns success if the channel was inexistent.
        """

        def check_success_message(tag):
            return 'successfully deleted' in tag.text

        # best guess if channel_id refers to a recorder
        recorder_id = None
        try:
            if channel_id.startswith('m'):
                r = channel_id.split('m')
                recorder_id = r[1]
        except IndexError:
            # will not guess and use channel_id as is
            pass

        params = {'deleteid': channel_id,
                'deletemode': 'trash'}
        path = '/admin/recorder%s/archive' % recorder_id if recorder_id \
                else '/admin/channel%s/status' % channel_id
        check_success = [
                {'emsg': 'successful deletion message not found',
                    'func': check_success_message}]

        return WebUiConfig.configuration(
                client=client,
                params=params,
                path=path,
                check_success=check_success)


    @classmethod
    def create_recorder(cls, client):
        return cls.create_channel_or_recorder(client, create_channel=False)


    @classmethod
    def rename_recorder(cls, client, recorder_id, recorder_name):
        return cls.rename_channel(client, 'm%s' % recorder_id, recorder_name)


    @classmethod
    def set_recorder_channels(cls, client, recorder_id, channel_list):
        """returns true or raise exception."""

        # note in this case, checks won't catch channels that are _not_
        # supposed to be configured, if the ones that are supposed to be
        # configured are correct.
        check_success = []
        for i in channel_list:
            check_success.append({
                'emsg': 'channel(%s) missing for recorder(%s) config' % \
                        (i, recorder_id),
                        'func': WebUiConfig.check_multivalue_select_funcfactory(\
                                name='rc[]', value=i)} )

        channel_list_param = [('rc[]', x) for x in channel_list]
        params = [('pfd_form_id', 'recorder_channels')] + channel_list_param
        path = '/admin/recorder%s/archive' % recorder_id

        return WebUiConfig.configuration(
                client=client,
                params=params,
                path=path,
                check_success=check_success)


    @classmethod
    def set_recorder_settings(cls, client, recorder_id,
            recording_timelimit_in_minutes=360, # 6h
            recording_sizelimit_in_kilobytes=64000000, # 64G
            output_format='avi', # or mov, mp4, ts(mpeg-ts)
            user_prefix='',      # prefix for recording file
            afu_enabled='on',    # this means auto-upload disabled!
            upnp_enabled=None):

        #
        # 06jun16 naomi: upnp and afu(automatic file upload) have dependencies
        # that are not treated by this api call -- these features must be enabled
        # for the device and configured in 'automatic file upload' and 'UPnP'
        # webui calls to be implemented in epipearl.endpoints.webui_config.
        #

        timelimit = '%d:%02d:00' % (recording_timelimit_in_minutes/60,
                recording_timelimit_in_minutes%60)

        check_success = [
                {'emsg': 'timelimit expected(%s)' % timelimit,
                    'func': WebUiConfig.check_singlevalue_select_funcfactory(
                        value=timelimit)},
                {'emsg': 'sizelimit expected(%s)' % recording_sizelimit_in_kilobytes,
                    'func': WebUiConfig.check_singlevalue_select_funcfactory(
                        value=str(recording_sizelimit_in_kilobytes))},
                {'emsg': 'output_format expected(%s)' % output_format,
                    'func': WebUiConfig.check_singlevalue_select_funcfactory(
                        value=output_format)},
                {'emsg': 'user_prefix expected(%s)' % user_prefix,
                    'func': WebUiConfig.check_input_id_value_funcfactory(
                        tag_id='user_prefix', value=user_prefix)}]
        params = {'pfd_form_id': 'rec_settings',
                'timelimit': timelimit,
                'sizelimit': recording_sizelimit_in_kilobytes,
                'output_format': output_format,
                'user_prefix': user_prefix,
                'afu_enabled': afu_enabled,
                'upnp_enabled': upnp_enabled}
        path = '/admin/recorder%s/archive' % recorder_id

        return WebUiConfig.configuration(
                client=client,
                params=params,
                path=path,
                check_success=check_success)


    @classmethod
    def delete_recorder(cls, client, recorder_id):
        """returns true or raises exception.

        param: recorder_id: number id for a recorder.
            e.g. recorder_id = 2 (corresponding channel_id is 'm2')
        """
        return cls.delete_channel(client, 'm%s'% recorder_id)
