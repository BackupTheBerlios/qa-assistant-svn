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

sys.path.extend((os.path.join(os.environ['srcdir'], '..'),
    os.environ['srcdir']))

import testchecklist
import testcreation

if __name__ == '__main__':
    suiteCheck = unittest.makeSuite(testchecklist.TestCheckList, 'test')
    suiteCreate = unittest.makeSuite(testcreation.TestCreation, 'test')
    alltests = unittest.TestSuite((suiteCreate, suiteCheck))
    result = unittest.TextTestRunner(verbosity=2).run(alltests)
    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)
