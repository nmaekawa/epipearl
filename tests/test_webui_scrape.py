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

    def test_scrape_mhcfg_form_values_ok(self, mhcfg_values):
        resp_html = resp_datafile('get_mhcfg', 'ok')
        doc = BeautifulSoup(resp_html, 'html.parser')
        form = doc.find('form')

        r = webui_scrape.pluck_form_values(bs4_form=form)
        assert r == mhcfg_values


    def test_scrape_radio_select_form_values_ok(self, date_and_time_values):
        resp_html = resp_datafile('set_date_and_time', 'ok')
        doc = BeautifulSoup(resp_html, 'html.parser')
        form = doc.find('form')

        r = webui_scrape.pluck_form_values(bs4_form=form)
        assert r == date_and_time_values


    def test_scrape_example_form_ok(self, example_form_values):
        resp_html = resp_datafile('set_example_form', 'ok')
        doc = BeautifulSoup(resp_html, 'html.parser')
        form = doc.find('form')

        r = webui_scrape.pluck_form_values(bs4_form=form)
        assert r == example_form_values


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
