#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_webui_config_endpoints
----------------------------------

Tests for `epipearl` config ui endpoints

"""

import os
os.environ['TESTING'] = 'True'

from bs4 import BeautifulSoup

import pytest
import httpretty

from conftest import resp_datafile
from conftest import example_form_values
from epipearl import Epipearl
from epipearl.endpoints.webui_config import WebUiConfig
from epipearl.errors import IndiscernibleResponseFromWebUiError
from epipearl.errors import SettingConfigError

epiphan_url = "http://fake.example.edu"
epiphan_user = "user"
epiphan_passwd = "passwd"

# control skipping live tests according to command line option --runlive
# requires env vars EPI_URL, EPI_USER, EPI_PASSWD, EPI_PUBLISH_TYPE
livetest = pytest.mark.skipif(
        not pytest.config.getoption("--runlive"),
        reason=(
            "need --runlive option to run, plus env vars",
            "EPI_URL, EPI_USER, EPI_PASSWD, EPI_PUBLISH_TYPE"))


class TestConfiguration(object):

    def setup_method(self, method):
        self.c = Epipearl(epiphan_url, epiphan_user, epiphan_passwd)

    @httpretty.activate
    def test_set_ntp_ok(self):
        resp_data = resp_datafile('set_date_and_time', 'ok')
        httpretty.register_uri(
                httpretty.POST,
                '%s/admin/timesynccfg' % epiphan_url,
                body=resp_data)

        response = WebUiConfig.set_ntp(
                client=self.c,
                server='north-america.pool.ntp.org',
                timezone='US/Alaska')
        assert response is True


    @httpretty.activate
    def test_set_ntp_invalid_tz(self):
        resp_data = resp_datafile('set_date_and_time', 'invalid_tz')
        httpretty.register_uri(
                httpretty.POST,
                '%s/admin/timesynccfg' % epiphan_url,
                body=resp_data)

        with pytest.raises(SettingConfigError) as e:
            response = WebUiConfig.set_ntp(
                    client=self.c,
                    server='north-america.pool.ntp.org',
                    timezone='Kawabonga')
        assert 'Unsupported time zone' in e.value.message


    @httpretty.activate
    def test_set_ntp_proto_didnot_take(self):
        resp_data = resp_datafile('set_date_and_time', 'proto_didnot_take')
        httpretty.register_uri(
                httpretty.POST,
                '%s/admin/timesynccfg' % epiphan_url,
                body=resp_data)

        with pytest.raises(SettingConfigError) as e:
            response = WebUiConfig.set_ntp(
                    client=self.c,
                    server='north-america.pool.ntp.org',
                    timezone='US/Alaska')
        assert 'protocol setting expected(NTP)' in e.value.message


    @httpretty.activate
    def test_set_source_deinterlacing_ok(self):
        resp_data = resp_datafile('set_source_deinterlacing', 'ok')
        httpretty.register_uri(
                httpretty.POST,
                '%s/admin/sources/D12345678.hdmi-a' % epiphan_url,
                body=resp_data,
                status=200)

        response = WebUiConfig.set_source_deinterlacing(
                client=self.c, source_name='D12345678.hdmi-a')
        assert response


    @httpretty.activate
    def test_set_source_deinterlacing_didnot_take(self):
        resp_data = resp_datafile('set_source_deinterlacing', 'ok')
        httpretty.register_uri(
                httpretty.POST,
                '%s/admin/sources/D12345678.hdmi-a' % epiphan_url,
                body=resp_data,
                status=200)

        with pytest.raises(SettingConfigError) as e:
            response = WebUiConfig.set_source_deinterlacing(
                    client=self.c, source_name='D12345678.hdmi-a',
                    enabled=False)
        assert 'deinterlacing expected to be OFF' in e.value.message


    @livetest
    def test_live_set_touchscreen(self):
        ca_url = os.environ['EPI_URL']
        epi = Epipearl(
                ca_url, os.environ['EPI_USER'], os.environ['EPI_PASSWD'])

        response = WebUiConfig.set_touchscreen(
                client=epi,
                screen_timeout=453)

        assert response is True


    @httpretty.activate
    def test_get_configuration(self):
        resp_data = resp_datafile('set_example_form', 'ok')
        httpretty.register_uri(
                httpretty.GET,
                '{}/admin/sources/D12345678.hdmi-a'.format(epiphan_url),
                body=resp_data,
                status=200)
        response = WebUiConfig.handle_form(
                client=self.c, path='/admin/sources/D12345678.hdmi-a',
                form_name='form_example')

        # TODO: how to use pytest fixtures with httpretty?
        #   there's something in the scope, or order of defs that i'm not
        #   getting right...
        assert response == example_form_values()


    @httpretty.activate
    def test_set_configuration(self):
        resp_data = resp_datafile('set_example_form', 'ok')
        example_values = example_form_values()
        httpretty.register_uri(
                httpretty.POST,
                '{}/admin/sources/D12345678.hdmi-a'.format(epiphan_url),
                body=resp_data,
                status=200)
        response = WebUiConfig.handle_form(
                client=self.c, path='/admin/sources/D12345678.hdmi-a',
                form_name='form_example', params=example_values)

        assert response == example_values


    @httpretty.activate
    def test_get_configuration_multiple_forms(self):
        resp_data = resp_datafile('set_example', 'multiple_forms')
        httpretty.register_uri(
                httpretty.GET,
                '{}/admin/sources/D12345678.hdmi-a'.format(epiphan_url),
                body=resp_data,
                status=200)
        with pytest.raises(IndiscernibleResponseFromWebUiError) as e:
            response = WebUiConfig.handle_form(
                    client=self.c, path='/admin/sources/D12345678.hdmi-a',
                    form_name='form_example')

        assert 'zero or more than one form' in e.value.message


    @httpretty.activate
    def test_get_configuration_no_form(self):
        resp_data = resp_datafile('set_example', 'no_form')
        httpretty.register_uri(
                httpretty.GET,
                '{}/admin/sources/D12345678.hdmi-a'.format(epiphan_url),
                body=resp_data,
                status=200)
        with pytest.raises(IndiscernibleResponseFromWebUiError) as e:
            response = WebUiConfig.handle_form(
                    client=self.c, path='/admin/sources/D12345678.hdmi-a',
                    form_name='form_example')

        assert 'zero or more than one form' in e.value.message


    @httpretty.activate
    def test_get_configuration_error_message(self):
        resp_data = resp_datafile('set_example', 'error_message')
        httpretty.register_uri(
                httpretty.GET,
                '{}/admin/sources/D12345678.hdmi-a'.format(epiphan_url),
                body=resp_data,
                status=200)
        with pytest.raises(SettingConfigError) as e:
            response = WebUiConfig.handle_form(
                    client=self.c, path='/admin/sources/D12345678.hdmi-a',
                    form_name='form_example')

        assert 'fake error message' in e.value.message
