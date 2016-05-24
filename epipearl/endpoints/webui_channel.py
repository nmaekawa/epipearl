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
    def create_channel(cls, client):
        """returns channel_id just created or exception."""
        path = '/admin/add_channel.cgi'
        try:
            r = client.get(path=path)
        except (requests.HTTPError,
                requests.RequestException,
                requests.ConnectionError,
                requests.Timeout) as e:
            msg = 'failed to call %s/admin/add_channel.cgi - %s' \
                    % (client.url, e.message)
            logger = logging.getLogger(__name__)
            logger.warning(msg)
            raise

        else:
            # requests.get will follow the redirect and return 200
            # but keep in response.history the 302 that we want
            msg = 'failed call to %s/%s ' % (client.url, path)
            logger = logging.getLogger(__name__)

            if r.status_code == 200:
                if not r.history: # status 200 is bad in this case
                    msg += '- expect response status 302, but got (%s)' % r.status_code
                    logger.warning(msg)
                    raise IndiscernibleResponseFromWebUiError(msg)

                if r.history[0].status_code != 302:
                    msg += '- expect response STATUS 302, but got (%s)' \
                            % r.history[0].status_code
                    logger.warning(msg)
                    raise IndiscernibleResponseFromWebUiError(msg)

                if 'location' in r.history[0].headers: # this is actually success
                    p = re.findall(r'/admin/channel(\d+)',
                            r.history[0].headers['location'])
                    if len(p) == 1:
                        return p[0]  # SUCCESS!
                    else:
                        msg += '- cannot parse channel created from location header(%s)' \
                                % r.history[0].headers['location']
                        logger.warning(msg)
                        raise IndiscernibleResponseFromWebUiError(msg)

                else: # 302, no header location found
                    msg += ' - missing header location for response status 302'
                    logger.warning(msg)
                    raise IndiscernibleResponseFromWebUiError(msg)

            else:
                if r.status_code == 302:
                    # this means that the location header is not present, otherwise
                    # requests.get would follow the redirect and return 200
                    msg += '- location header missing.'
                else: # status code not expected (!= 302)
                    msg += ' - expect response status 302, but GOT (%s)' % r.status_code
                logger.warning(msg)
                raise IndiscernibleResponseFromWebUiError(msg)

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
            logger = logging.getLogger(__name__)
            logger.warning(msg)
            raise e
        else:
            if r.status_code == 200:  # all went well
                return channel_name
            raise IndiscernibleResponseFromWebUiError(
                   'failed to call %s/%s - response status(%s)' % \
                           (client.url, path, r.status_code))


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
            logger = logging.getLogger(__name__)
            logger.warning(msg)
            raise e
        else:
            if r.status_code == 200:
                return r.text
            raise IndiscernibleResponseFromWebUiError(
                    'failed to call %s/%s - response status(%s)' % \
                            (client.url, path, r.status_code))

    @classmethod
    def set_channel_rtmp(cls, client, channel_id,
            rtmp_url, rtmp_stream, rtmp_usr, rtmp_pwd):
        """returns true or raises exception."""

        def check_rtmp_url(tag):
            return tag.has_attr('id') and \
                    tag['id'] == 'rtmp_url' and \
                    tag.has_attr('value') and \
                    tag['value'] == rtmp_url

        def check_rtmp_stream(tag):
            return tag.has_attr('id') and \
                    tag['id'] == 'rtmp_stream' and \
                    tag.has_attr('value') and \
                    tag['value'] == rtmp_stream

        def check_rtmp_usr(tag):
            return tag.has_attr('id') and \
                    tag['id'] == 'rtmp_username' and \
                    tag.has_attr('value') and \
                    tag['value'] == rtmp_usr

        def check_rtmp_pwd(tag):
            return tag.has_attr('id') and \
                    tag['id'] == 'rtmp_password' and \
                    tag.has_attr('value') and \
                    tag['value'] == rtmp_pwd

        params = {'rtmp_url': rtmp_url,
                'rtmp_stream': rtmp_stream,
                'rtmp_username': rtmp_usr,
                'rtmp_password': rtmp_pwd}

        path = '/admin/channel%s/streamsetup' % channel_id

        check_success = [
                {'emsg': 'rtmp_usr expected(%s)' % rtmp_usr,
                    'func': check_rtmp_usr},
                {'emsg': 'rtmp_url expected(%s)' % rtmp_url,
                    'func': check_rtmp_url},
                {'emsg': 'rtmp_stream expected(%s)' % rtmp_stream,
                    'func': check_rtmp_stream},
                {'emsg': 'not the rtmp_pwd expected',
                    'func': check_rtmp_pwd}]

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
    def create_recorder(cls, client, params, check_success):
        raise NotImplementedError('create_recorder() not implemented yet.')

    @classmethod
    def set_recorder_channels(cls, client, params, check_success):
        raise NotImplementedError(
                'set_recorder_channels() not implemented yet.')

    @classmethod
    def set_recorder_settings(cls, client, params, check_success):
        raise NotImplementedError(
                'set_recorder_settings() not implemented yet.')

    @classmethod
    def delete_recorder(cls, client, recorder_id):
        """returns true or raises exception.

        param: recorder_id: number id for a recorder.
            e.g. recorder_id = 2 (corresponding channel_id is 'm2')
        """
        return cls.delete_channel(client, 'm%s'% recorder_id)


    @classmethod
    def update_firmware(cls, client, params, check_success):
        raise NotImplementedError('update_firmware() not implemented yet.')

    #
    # dce custom api
    #

    @classmethod
    def set_mhpearl_settings(cls, settings):
        raise NotImplementedError(
                'set_mhpearl_settings() not implemented yet.')
