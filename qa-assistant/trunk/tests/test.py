#! /usr/bin/python
#
# File: test.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 24 September, 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
'''Automated testing harness to drive the unittests for QA Assistant.
'''
__revision__ = '$Rev$'

import sys
import os
import unittest

if os.environ.has_key('srcdir'):
    srcdir = os.environ['srcdir']
else:
    srcdir = '.'
sys.path.extend((os.path.join(srcdir, '..'), srcdir, '..'))

import testcreation
import testchecklist
import testtreetips

if __name__ == '__main__':
    createSuite = testcreation.suite()
    checkSuite = testchecklist.suite()
    treetipSuite = testtreetips.suite()
    suite = unittest.TestSuite((createSuite, treetipSuite, checkSuite))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)
