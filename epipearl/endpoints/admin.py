# -*- coding: utf-8 -*-
"""http api and web ui calls to epiphan pearl."""

from bs4 import BeautifulSoup
import logging
import requests

from epipearl.errors import RequestsError
from epipearl.errors import SettingConfigError

class Admin(object):
    """calls to admin api that return json or key,value responses.

    in general, methods require arguments below
    client: epipearl client
    channel: epiphan channel call refers to
    params: dict with params to call

    in general, methods return dict below
    {'status_code': int http status code,
     'response_text': string with body of response}
    """

    @classmethod
    def get_params(cls, client, channel, params=None):
        if params is None:
            params = {}
        r = client.get(
                'admin/channel%s/get_params.cgi' % channel,
                params=params)
        return {
            'status_code': r.status_code,
            'response_text': r.text}

    @classmethod
    def set_params(cls, client, channel, params):
        r = client.get(
                'admin/channel%s/set_params.cgi' % channel,
                params=params)
        return {
            'status_code': r.status_code,
            'response_text': ''}


class AdminWebUi(object):

    @classmethod
    def set_date_and_time(cls, client, params, check_success):
        """config settings for date_and_time

        params: dict with params for date_and_time web ui form
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
                    'admin/timesynccfg',
                    data=params)
        except requests.HTTPError as e:
            return {
                'status_code': r.status_code,
                'error_msg': e.message,
                'response': r}
        except (requests.RequestException,
                requests.ConnectionError,
                requests.Timeout) as e:
            msg = 'set_date_and_time() failed to call %s' % client.url
            msg += '/admmin/timesynccfg'
            logger = logging.getLogger()
            logger.warning(msg)
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

