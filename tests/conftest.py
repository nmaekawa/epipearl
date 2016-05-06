# -*- coding: utf-8 -*-

import os
import pytest

cwd = os.getcwd()

def pytest_addoption( parser ):
    parser.addoption("--runlive", action="store_true",
        help="test with live capture agents" )


def resp_html_data(config_type, error_type=None):
    test_data = config_type
    if error_type:
        test_data = '_'.join([config_type, error_type])

    filename = os.path.join(cwd, 'tests/resp_%s.html' % test_data)
    data = ''
    with open(filename, 'r') as myfile:
        data = myfile.read()

    return data
