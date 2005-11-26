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

sys.path.extend((os.path.join(srcdir, '..', 'src'),
    os.path.join('..', 'src'),
    os.path.join(srcdir, '..', 'data'),
    os.path.join('..', 'data')
    ))

import creationtest
import checklisttest
import treetipstest
import propertiestest
import qaconverttest

if __name__ == '__main__':
    createSuite = creationtest.suite()
    propertiesSuite = propertiestest.suite()
    checkSuite = checklisttest.suite()
    treetipSuite = treetipstest.suite()
    qaconvertSuite = qaconverttest.suite()
    suite = unittest.TestSuite((createSuite, treetipSuite, propertiesSuite,
        checkSuite, qaconvertSuite))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)
