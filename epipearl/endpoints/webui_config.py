# -*- coding: utf-8 -*-
"""http api and web ui calls to epiphan pearl."""

from bs4 import BeautifulSoup
import logging
import requests
import re

from epipearl.errors import RequestsError
from epipearl.errors import SettingConfigError


class WebUiConfig(object):
    """calls to epiphan pearl web ui.

    these are not non-documented calls, so can break if epiphan
    changes its webui interface. and beware that these are design
    to fit dce config reqs!

    use at your own peril!!!!

    methods below send forms (or gets) to the web ui.
    """

    @classmethod
    def set_ntp(cls, client, server, timezone):
        # funcs to webscrape response page for success or error
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
                {'emsg': 'protocol setting expected(NTP)',
                    'func': check_ntp_proto},
                {'emsg': 'expected to enable sync(auto)',
                    'func': check_ntp_sync},
                {'emsg': 'expected ntp server(%s)' % server,
                    'func': check_ntp_server}]

        return cls.configuration(
                client=client,
                path='admin/timesynccfg',
                params=params,
                check_success=check_success)


    @classmethod
    def set_touchscreen(cls, client, screen_timeout=600):
        # funcs to webscrape response page for success or error
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

        return cls.configuration(
                client=client,
                path='admin/touchscreencfg',
                params=params,
                check_success=check_success)

    @classmethod
    def set_remote_support_and_permanent_logs(cls, client, log_enabled=True):
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

        return  cls.configuration(
                client=client,
                path='admin/maintenancetfg',
                params=params,
                check_success=check_success)


    @classmethod
    def configuration(cls, client, params, check_success, path):
        """generic request to config form

        client: epipearl client instance
        path: for webui function, ex: admin/timesynccfg
        params: dict with params for web ui form
        check_success: list of dicts
            [{ 'func': <function for BeautifulSoup.find>
               'emsg': string error msg if func returns false }]
        """
        try:
            r = client.post(
                    path,
                    data=params)
        except (requests.HTTPError,
                requests.RequestException,
                requests.ConnectionError,
                requests.Timeout) as e:
            msg = 'failed to call %s/%s - %s' % (client.url, path, e.message)
            logger = logging.getLogger(__name__)
            logger.warning(msg)
            raise
        else:
            msg = 'failed to call %s/%s ' % (client.url, path)
            logger = logging.getLogger(__name__)
            # still have to check errors in response html
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                emsg = cls._scrape_error(soup)
                if len(emsg) > 0:     # concat error messages
                    allmsgs = [x['msg'] for x in emsg if 'msg' in x]
                    msg += '\n'.join(allmsgs)
                    logger.warning(msg)
                    raise SettingConfigError(msg)
                else:
                    # no error msg, check that updates took place
                    for c in check_success:
                        tags = soup.find_all(c['func'])
                        if not tags:
                            msg += '- %s' % c['emsg']
                            logger.warning(msg)
                            raise SettingConfigError(msg)
                # all is well
                return True

            raise IndiscernibleResponseFromWebUiError(
                    'failed to call %s/%s - response status(%s)' % \
                            (client.url, path, r.status_code))


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
