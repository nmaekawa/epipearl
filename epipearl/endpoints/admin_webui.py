# -*- coding: utf-8 -*-
"""http api and web ui calls to epiphan pearl."""

from bs4 import BeautifulSoup
import logging
import requests

from epipearl.errors import RequestsError
from epipearl.errors import SettingConfigError


class AdminWebUi(object):
    """calls to epiphan pearl web ui.

    these are not non-documented calls, so can break if epiphan
    changes its webui interface. and beware that these are design
    to fit dce config reqs!

    use at your own peril!!!!

    methods below send forms (or gets) to the web ui.
    """

    @classmethod
    def configuration(cls, client, params, check_success, path):
        """config settings for date_and_time

        client: epipearl client instance
        path: for webui function, ex: admin/timesynccfg
        params: dict with params for web ui form
        check_success: list of dicts
            [{ 'func': <function for BeautifulSoup.find>
               'emsg': string error msg if func returns false }]

        returns: {
            'status_code': <http response status_code>
            'error_msg': string with error msg, if error occurred
            'response': dict with key,value
        """
        try:
            r = client.post(
                    path,
                    data=params)
        except requests.HTTPError as e:
            return {
                'status_code': r.status_code,
                'error_msg': e.message,
                'response': r}
        except (requests.RequestException,
                requests.ConnectionError,
                requests.Timeout) as e:
            msg = 'failed to call %s/%s' % (client.url, path)
            logger = logging.getLogger()
            logger.warning('%s : %s' % (msg, e.message))
            raise RequestsError(msg, e)
        else:
            # still have to check errors in response html
            soup = BeautifulSoup(r.text, 'html.parser')
            emsg = cls._scrape_error(soup)
            if len(emsg) > 0:     # concat error messages
                allmsgs = [x['msg'] for x in emsg if 'msg' in x]
                msgs = '\n'.join(allmsgs)
                raise SettingConfigError(msgs)
            else:
                # no error msg, check that updates took place
                for c in check_success:
                    tags = soup.find_all(c['func'])
                    if not tags:
                        return {'status_code': 400,
                            'error_msg': c['emsg'],
                            'response': None}

            # all is well
            return {'status_code': 200,
                    'error_msg': '', 'response': None}


    @classmethod
    def _scrape_error(cls, soup):
        """webscrape for error msg in returned html."""
        warn = soup('div', class_='wui-message-warning')
        msgs = cls._scrape_msg(warn)
        error = soup('div', class_='wui-message-error')
        msgs += cls._scrape_msg(error, warning=False)
        return msgs


    @classmethod
    def _scrape_msg(cls, mtag, warning=True):
        """navigate div to find msg text and error code."""
        resp = []
        if len(mtag) > 0:
            dtag = mtag[0].findChildren('div',
                    class_='wui-message-banner-inner')
            for d in dtag:
                lines = d.strings
                error_msg = None
                error_code = None
                try:
                    error_msg = next(lines)
                    error_code = next(lines)
                except StopIteration:
                    # msg or code or both not found!
                    pass
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.warning(
                            'could not scrape epiphan webui response: %s' \
                                    % e.message)
                else:
                    # msg and code ok
                    resp.append({
                        'cat': 'warning' if warning else 'error',
                        'msg': error_msg if error_msg else 'unknown msg',
                        'code': error_code if error_code else 'unknown code'})
        return resp


    @classmethod
    def create_channel(cls, client, params, check_success):
        raise NotImplementedError('create_channel() not implemented yet.')

    @classmethod
    def set_channel_layout(cls, client, params, check_success):
        raise NotImplementedError('set_channel_layout() not implemented yet.')

    @classmethod
    def set_channel_rtmp(cls, client, params, check_success):
        raise NotImplementedError('set_channel_rtmp() not implemented yet.')

    @classmethod
    def delete_channel(cls, client, params, check_success):
        raise NotImplementedError('delete_channel() not implemented yet.')

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
    def delete_recorder(cls, client, params, check_success):
        raise NotImplementedError('delete_recorder() not implemented yet.')

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
