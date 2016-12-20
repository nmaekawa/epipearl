# -*- coding: utf-8 -*-

import os
import pytest


cwd = os.getcwd()


def pytest_addoption(parser):
    parser.addoption(
            "--runlive", action="store_true",
            help="test with live capture agents")


def resp_datafile(config_type, error_type=None, ext='html'):
    test_data = config_type
    if error_type:
        test_data = '_'.join([config_type, error_type])

    filename = os.path.join(cwd, 'tests/resp_%s.%s' % (test_data, ext))
    data = ''
    with open(filename, 'r') as myfile:
        data = myfile.read()

    return data


@pytest.fixture(scope='module')
def mhcfg_values():
    return {
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


@pytest.fixture(scope='module')
def date_and_time_values():
    return {
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
            'tz': ['US/Alaska']
    }


@pytest.fixture(scope='module')
def example_form_values():
    return {
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
