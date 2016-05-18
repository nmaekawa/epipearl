#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_config
----------------------------------

Tests for `epipearl` admin ui endpoints

these compliments test_configs.py where some errors cannot be
emulated via the epipearl functions.
"""

import os
os.environ['TESTING'] = 'True'

import pytest
import requests
import httpretty
from sure import expect, should, should_not

from conftest import resp_html_data
from epipearl import Epipearl
from epipearl.endpoints.admin_webui import AdminWebUi
from epipearl.errors import SettingConfigError

epiphan_url = "http://fake.example.edu"
epiphan_user = "user"
epiphan_passwd = "passwd"

# control skipping live tests according to command line option --runlive
# requires env vars EPI_URL, EPI_USER, EPI_PASSWD, EPI_PUBLISH_TYPE
livetest = pytest.mark.skipif(
        not pytest.config.getoption( "--runlive" ),
        reason = ( "need --runlive option to run, plus env vars",
            "EPI_URL, EPI_USER, EPI_PASSWD, EPI_PUBLISH_TYPE" ) )


class TestConfiguration(object):

    def setup( self ):
        self.c = Epipearl(epiphan_url, epiphan_user, epiphan_passwd)
        #params = {'pdf_form_id': 'fn_episcreen', 'epiScreenEnabled': 'on',
        #        'epiScreenTimeout': 123 'showVideo': 'on', 'showInfo': 'on'}

    @httpretty.activate
    def test_set_ntp_ok(self):
        resp_data = resp_html_data('set_date_and_time', 'ok')
        httpretty.register_uri(httpretty.POST,
                '%s/date_and_time_ntp_ok' % epiphan_url,
                body=resp_data)

        params = {'server': 'north-america.pool.ntp.org',
                'tz': 'US/Alaska', 'fn': 'date', 'rdate': 'auto',
                'rdate_proto': 'NTP'}
        checks = [{'func': self._check_ntp_proto, 'emsg': 'should not happen!'}]
        response = AdminWebUi.configuration(
                client=self.c,
                path='date_and_time_ntp_ok',
                params=params, check_success=checks)
        assert response['status_code'] == 200


    @httpretty.activate
    def test_set_ntp_invalid_proto(self):
        resp_data = resp_html_data('set_date_and_time', 'invalid_proto')
        httpretty.register_uri(httpretty.POST,
                '%s/date_and_time_invalid_proto' % epiphan_url,
                body=resp_data)

        params = {'server': 'north-america.pool.ntp.org',
                'tz': 'US/Alaska', 'fn': 'date', 'rdate': 'auto',
                'rdate_proto': 'NTP'}
        checks = [{'func': self._check_ntp_proto, 'emsg': 'proto did not take'}]
        with pytest.raises(SettingConfigError) as e:
            response = AdminWebUi.configuration(
                    client=self.c,
                    path='date_and_time_invalid_proto',
                    params=params, check_success=checks)
        assert 'choose valid time synchronization protocol' in e.value.message


    @httpretty.activate
    def test_set_ntp_proto_didnot_take(self):
        resp_data = resp_html_data('set_date_and_time', 'proto_didnot_take')
        httpretty.register_uri(httpretty.POST,
                '%s/date_and_time_proto_error' % epiphan_url,
                body=resp_data)

        params = {'server': 'north-america.pool.ntp.org',
                'tz': 'US/Alaska', 'fn': 'date', 'rdate': 'auto',
                'rdate_proto': 'NTP'}
        checks = [{'func': self._check_ntp_proto, 'emsg': 'proto didnot take'}]
        response = AdminWebUi.configuration(
                client=self.c,
                path='date_and_time_proto_error',
                params=params, check_success=checks)
        assert int(response['status_code']) == 400
        assert 'proto didnot take' in response['error_msg']

    #
    # how not to repeat these functions from epipearl.Epipearl
    # if i need closure in most of them?
    #
    def _check_ntp_proto(self, tag):
        return tag.name == 'option' and \
                tag.has_attr('selected') and \
                tag.has_attr('value') and \
                tag['value'] == 'NTP'


