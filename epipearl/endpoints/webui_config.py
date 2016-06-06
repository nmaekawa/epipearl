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
    def check_singlevalue_checkbox_funcfactory(cls, tag_id):
        def f(tag):
            return tag.has_attr('id') and \
                    tag['id'] == tag_id and \
                    tag.has_attr('checked')
        return f

    @classmethod
    def check_singlevalue_checkbox_disabled_funcfactory(cls, tag_id):
        def f(tag):
            return tag.has_attr('id') and \
                    tag['id'] == tag_id and \
                    not tag.has_attr('checked')
        return f

    @classmethod
    def check_singlevalue_select_funcfactory(cls, value):
        def f(tag):
            return tag.has_attr('selected') and \
                    tag.has_attr('value') and \
                    tag['value'] == value
        return f

    @classmethod
    def check_multivalue_select_funcfactory(cls, name, value):
        def f(tag):
            return tag.has_attr('checked') and \
                    tag.has_attr('name') and \
                    tag['name'] == name and \
                    tag['value'] == value
        return f

    @classmethod
    def check_input_id_value_funcfactory(cls, tag_id, value):
        def f(tag):
            return tag.has_attr('id') and \
                    tag['id'] == tag_id and \
                    tag['value'] == value
        return f

    @classmethod
    def set_ntp(cls, client, server, timezone):
        params = {'server': server, 'tz': timezone,
                'fn': 'date', 'rdate': 'auto', 'rdate_proto': 'NTP'}

        check_success = [
                {'emsg': 'timezone setting expected(%s)' % timezone,
                    'func': cls.check_singlevalue_select_funcfactory(value=timezone)},
                {'emsg': 'protocol setting expected(NTP)',
                    'func': cls.check_singlevalue_select_funcfactory(value='NTP')},
                {'emsg': 'expected to enable sync(auto)',
                    'func': cls.check_singlevalue_checkbox_funcfactory(
                        tag_id='rdate_auto')},
                {'emsg': 'expected ntp server(%s)' % server,
                    'func': cls.check_input_id_value_funcfactory(
                        tag_id='server', value=server)}]
        return cls.configuration(
                client=client,
                path='admin/timesynccfg',
                params=params,
                check_success=check_success)


    @classmethod
    def set_touchscreen(cls, client, screen_timeout=600):
        params = {'pdf_form_id': 'fn_episcreen',
                'epiScreenEnabled': 'on',
                'epiScreenTimeout': screen_timeout,
                'showVideo': 'on',
                'showInfo': 'on'}

        check_success = [
                {'emsg': 'epiScreenEnabled ON expected',
                    'func': cls.check_singlevalue_checkbox_funcfactory(
                        tag_id='epiScreenEnabled')},
                {'emsg': 'epiScreenTimeout expected(%s)' % screen_timeout,
                    'func': cls.check_input_id_value_funcfactory(
                        tag_id='epiScreenTimeout', value=screen_timeout)},
                {'emsg': 'showPreview ON expected',
                    'func': cls.check_singlevalue_checkbox_funcfactory(
                        tag_id='showVideo')},
                {'emsg': 'showSystemStatus ON expected',
                    'func': cls.check_singlevalue_checkbox_funcfactory(
                        tag_id='showInfo')},
                {'emsg': 'changeSettings OFF expected',
                    'func': cls.check_singlevalue_checkbox_disabled_funcfactory(
                        tag_id='changeSettings')},
                {'emsg': 'recordControl OFF expected',
                    'func': cls.check_singlevalue_checkbox_disabled_funcfactory(
                        tag_id='recordControl')} ]

        return cls.configuration(
                client=client,
                path='admin/touchscreencfg',
                params=params,
                check_success=check_success)

    @classmethod
    def set_remote_support_and_permanent_logs(cls, client, log_enabled=True):
        _default_server = 'epiphany.epiphan.com'
        _default_port = '30'

        params = {'enablessh': 'on',
                'tunnel': 'on',
                'tunnelsrv': _default_server,
                'tunnelport': _default_port}

        check_success = [
                {'emsg': 'remote_support ON expected',
                    'func': cls.check_singlevalue_checkbox_funcfactory(
                        tag_id='enabledssh')},
                {'emsg': 'server_connection ON expected',
                    'func': cls.check_singlevalue_checkbox_funcfactory(
                        tag_id='tunnel')},
                {'emsg': 'server_address expected(%s)' % _default_server,
                    'func': cls.check_input_id_value_funcfactory(
                        tag_id='tunnelsrv', value=_default_server)},
                {'emsg': 'server_port expected(%s)' % _default_port,
                    'func': cls.check_input_id_value_funcfactory(
                        tag_id='tunnelport', value=_default_port)}]

        if log_enabled:
            params['permanent_logs']= 'on'
            check_success.append(
                {'emsg': 'permanent logs expected to be ON',
                    'func': cls.check_singlevalue_checkbox_funcfactory(
                        tag_id='permanent_logs')})
        else:
            check_success.append(
                {'emsg': 'permanent logs expected to be OFF',
                    'func': cls.check_singlevalue_checkbox_disabled_funcfactory(
                        tag_id='permanent_logs')})

        return  cls.configuration(
                client=client,
                path='admin/maintenancetfg',
                params=params,
                check_success=check_success)


    @classmethod
    def update_firmware(cls, client, params, check_success):
        raise NotImplementedError('update_firmware() not implemented yet.')

    @classmethod
    def set_afu(cls, client):
        raise NotImplementedError('set_automatic_file_upload() not implemented yet.')

    @classmethod
    def set_upnp(cls, client):
        raise NotImplementedError(
                'set_universal_plug_and_play() not implemented yet.')


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
            msg = 'error from call %s/%s ' % (client.url, path)
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
                    'error in call %s/%s - response status(%s)' % \
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
