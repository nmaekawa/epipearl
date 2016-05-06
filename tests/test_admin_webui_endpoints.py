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
from epipearl.endpoints.admin import AdminWebUi
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


class TestConfig(object):

    def setup( self ):
        self.c = Epipearl(epiphan_url, epiphan_user, epiphan_passwd)


    @httpretty.activate
    def test_set_ntp_invalid_proto(self):
        resp_data = resp_html_data('set_date_and_time', 'invalid_proto')
        httpretty.register_uri(httpretty.POST,
                '%s/admin/timesynccfg' % epiphan_url,
                body=resp_data)

        params = {'server': 'north-america.pool.ntp.org',
                'tz': 'US/Alaska', 'fn': 'date', 'rdate': 'auto',
                'rdate_proto': 'NTP'}
        checks = [{'func': self._check_ntp_proto, 'emsg': 'proto did not take'}]
        with pytest.raises(SettingConfigError) as e:
            response = AdminWebUi.set_date_and_time(
                    client=self.c, params=params, check_success=checks)
        assert 'choose valid time synchronization protocol' in e.value.message


    #
    # how not to repeat these functions from epipearl.Epipearl
    # if i need closure in some of them?
    #
    def _check_ntp_proto(tag):
        return tag.name == 'option' and \
                tag.has_attr('selected') and \
                tag.has_attr('value') and \
                tag['value'] == 'NTP'


