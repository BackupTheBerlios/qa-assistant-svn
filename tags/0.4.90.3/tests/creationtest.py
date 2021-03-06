#!/usr/bin/python -tt
# File: creationtest.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 24 Sept 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
'''Tests creation of all the objects in QA Assistant.
'''
__revision__ = '$Rev$'

import os
import sys
import unittest
import gtk

import test

import error
import checklist
import checkview
import review

class TestCreation(unittest.TestCase):
    def setUp(self):
        self.dataDir = os.path.join(test.srcdir, '..', 'data')

    #
    # CheckView creation tests
    #
    def test_CheckViewCreateWithoutChecklist(self):
        self.assert_(isinstance(checkview.CheckView(), checkview.CheckView))
    
    def test_CheckViewCreateWithChecklist(self):
        check = checklist.CheckList(os.path.join(self.dataDir, 'fedoraus.xml'))
        self.assert_(isinstance(checkview.CheckView(check),
            checkview.CheckView))
       
    def test_CheckViewCreateNotACheckList(self):
        self.assertRaises(TypeError, checkview.CheckView, 1)

    ### FIXME: Add optionrenderer

    #
    # Review creation functions
    #
    def test_ReviewCreateSuccess(self):
        check = checklist.CheckList(os.path.join(self.dataDir, 'fedoraus.xml'))
        self.assert_(isinstance(review.Review(check), review.Review))

    def test_ReviewCreateNotACheckList(self):
        self.assertRaises(AssertionError, review.Review, 3)

def suite():
    highPriority = unittest.makeSuite(TestCreation, 'test0_')
    mediumPriority = unittest.makeSuite(TestCreation, 'test50_')
    otherPriority = unittest.makeSuite(TestCreation, 'test_')
    return unittest.TestSuite((highPriority, mediumPriority, otherPriority))

if __name__ == '__main__':
    suite = suite()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)
