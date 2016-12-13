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
from epipearl import Epipearl
from epipearl import SettingConfigError
from epipearl.endpoints.webui_config import WebUiConfig

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


class TestScrapeForValues(object):

    scraped_values = {
            'DEVICE_NAME': u'lab-2',
            'DEVICE_ADDRESS': u'http://device_fake_address.blah.blof.edu',
            'DEVICE_USERNAME': u'device_fake_user',
            'DEVICE_PASSWORD': u'device_fake_password',
            'DEVICE_CHANNEL': u'1',
            'DEVICE_LIVE_CHANNELS': u'2,3',
            'DEVICE_LIVE_STREAMS': u'''
                    {"streams": { "1920x540": "rtmp://cp111111.live.edgefcs.net/live/lab-2-presenter-delivery.stream-1920x540_1_200@888888" , "960x270": "rtmp://cp111111.live.edgefcs.net/live/lab-2-presenter-delivery.stream-960x270_1_200@111111"}}                ''',
            'MANAGE_LIVE': True,
            'FILE_SEARCH_RANGE': u'60',
            'ADMIN_SERVER_URL': u'admin_server_fake_url.compute-1.amazonaws.com',
            'ADMIN_SERVER_USER': u'admin_server_fake_user',
            'ADMIN_SERVER_PASSWD': u'admin_server_fake_pass',
            'UPDATE_FREQUENCY': u'120',
            'CONNECTTIMEOUT': u'60',
            'LOW_SPEED_TIME': u'300',
            'MAX_INGEST': u'1',
            'INGEST_DELAY': u'60',
            'NUMBER_OF_RETRIES': u'5',
            'BACKUP_AGENT': False,
        }

    def test_scrape_form_values_ok(self):
        resp_html = resp_datafile('get_mhcfg', 'ok')
        soup = BeautifulSoup(resp_html, 'html.parser')
        r = WebUiConfig.scrape_form_values(
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
        assert r == self.scraped_values



