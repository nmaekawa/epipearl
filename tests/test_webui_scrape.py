#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_webui_scrape
----------------------------------

"""

import os
os.environ['TESTING'] = 'True'

from bs4 import BeautifulSoup

import httpretty
import pprint
import pytest

from conftest import resp_datafile
import epipearl.endpoints.webui_scrape as webui_scrape


pp = pprint.PrettyPrinter(indent=4)


class TestScrapeForValues(object):

    mhcfg_values = {
            'DEVICE_NAME': 'lab-2',
            'DEVICE_ADDRESS': 'http://device_fake_address.blah.blof.edu',
            'DEVICE_USERNAME': 'device_fake_user',
            'DEVICE_PASSWORD': 'device_fake_password',
            'DEVICE_CHANNEL': '1',
            'DEVICE_LIVE_CHANNELS': '2,3',
            'DEVICE_LIVE_STREAMS': '''
                    {"streams": { "1920x540": "rtmp://cp111111.live.edgefcs.net/live/lab-2-presenter-delivery.stream-1920x540_1_200@888888" , "960x270": "rtmp://cp111111.live.edgefcs.net/live/lab-2-presenter-delivery.stream-960x270_1_200@111111"}}                ''',
            'MANAGE_LIVE': True,
            'FILE_SEARCH_RANGE': '60',
            'ADMIN_SERVER_URL': 'admin_server_fake_url.compute-1.amazonaws.com',
            'ADMIN_SERVER_USER': 'admin_server_fake_user',
            'ADMIN_SERVER_PASSWD': 'admin_server_fake_pass',
            'UPDATE_FREQUENCY': '120',
            'CONNECTTIMEOUT': '60',
            'LOW_SPEED_TIME': '300',
            'MAX_INGEST': '1',
            'INGEST_DELAY': '60',
            'NUMBER_OF_RETRIES': '5',
            'BACKUP_AGENT': False,
        }

    date_and_time_values = {
            'date': '2016-05-06',
            'fn': 'date',
            'localserver': False,
            'ptp_domain': ['_DFLT'],
            'ptp_localtime': False,
            'rdate': 'auto',
            'rdate_proto': ['NTP'],
            'rdate_secs': [],
            'server': 'north-america.pool.ntp.org',
            'time': '12:54:10',
            'tz': ['US/Alaska']}

    example_form_values = {
            'button_example_name': u'Button Testing',
            'checkbox_name': False,
            'form_name': u'date',
            'multi_radio_name': u'Awesome',
            'password_example_name': u'Secret',
            'select_example_name': [u'apple'],
            'single_radio_name': u'single_radio',
            'single_radio_BLANK': None,
            'input_with_no_type': None,
            'submit_example_name': u'Submit to Test',
            'text_example_name': u'NonSecret',
            'textarea_example_name': u"""
            long line text for an example textarea and because right now
            i'd rather be knitting i wish i had some worsted weight yarn and
            #8 needles to knit and purl a little pullover for myself...
        """,
    }


    def test_scrape_mhcfg_form_values_ok(self):
        resp_html = resp_datafile('get_mhcfg', 'ok')
        doc = BeautifulSoup(resp_html, 'html.parser')
        form = doc.find('form')

        r = webui_scrape.pluck_form_values(bs4_form=form)
        assert r == self.mhcfg_values


    def test_scrape_radio_select_form_values_ok(self):
        resp_html = resp_datafile('set_date_and_time', 'ok')
        doc = BeautifulSoup(resp_html, 'html.parser')
        form = doc.find('form')

        r = webui_scrape.pluck_form_values(bs4_form=form)
        pp.pprint(r)
        assert r == self.date_and_time_values


    def test_scrape_example_form_ok(self):
        resp_html = resp_datafile('set_example_form', 'ok')
        doc = BeautifulSoup(resp_html, 'html.parser')
        form = doc.find('form')

        r = webui_scrape.pluck_form_values(bs4_form=form)
        assert r == self.example_form_values


    def test_scrape_input_with_no_name(self):
        resp_html = resp_datafile('set_example_form', 'ok')
        doc = BeautifulSoup(resp_html, 'html.parser')
        form = doc.find('form')
        select = form.find('select')
        # remove attr `name` from select
        name = select['name']
        del(select['name'])

        r = webui_scrape.pluck_form_values(bs4_form=form)
        # just skip select element
        assert name not in r


    def test_scrape_select_with_no_value_selected(self):
        def find_selected(tag):
            return tag.has_attr('selected')

        resp_html = resp_datafile('set_example_form', 'ok')
        doc = BeautifulSoup(resp_html, 'html.parser')
        form = doc.find('form')
        select = form.find('select')
        name = select['name']
        selected = select.find(find_selected)
        # un-select option from dropdown
        del(selected['selected'])

        r = webui_scrape.pluck_form_values(bs4_form=form)
        # no option selected, return is an empty list
        assert len(r[name]) == 0


    def test_scrape_input_with_no_value(self):
        def find_checked(tag):
            return tag.has_attr('checked')

        radio_button_value = 'my favorite animal is poopies'

        resp_html = resp_datafile('set_example_form', 'ok')
        doc = BeautifulSoup(resp_html, 'html.parser')
        form = doc.find('form')
        checked = form.find(find_checked)
        name = checked['name']
        # remove attr `value` from checked radio-button
        checked.string = radio_button_value
        del(checked['value'])

        r = webui_scrape.pluck_form_values(bs4_form=form)
        pp.pprint(r)
        # replace value with tag.string
        assert r[name] == radio_button_value

        # remove tag.string
        checked.string = ''
        r = webui_scrape.pluck_form_values(bs4_form=form)
        assert r[name] == ''

