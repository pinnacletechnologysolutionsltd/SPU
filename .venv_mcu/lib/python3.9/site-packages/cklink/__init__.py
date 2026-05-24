# -*- coding:utf-8 -*-

__version__ = '0.0.1'
__title__ = 'pycklink'
__author__ = 'tanjiaxi'
__author_email__ = 'jxtan@bouffalolab.com'
__copyright__ = 'Copyright 2021 Bouffalo Lab'
__license__ = 'MIT'
__url__ = 'http://pypi.org/project/pycklink/'
__description__ = 'Python interface for CKLink.'
__long_description__ = '''This module provides a Python implementation of the
CKLink SDK by leveraging the SDK's DLL.
'''

from .cklink import *
from .structs import *
from .errors import *

