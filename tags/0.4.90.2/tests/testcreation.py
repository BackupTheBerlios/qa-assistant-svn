#!/usr/bin/python -tt
# File: testcreation.py
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
import treetips
import review

class TestCreation(unittest.TestCase):
    def setUp(self):
        self.dataDir = os.path.join(test.srcdir, '..', 'data')

    #
    # CheckList creation tests
    #
    def test0_ChecklistCreateSuccess(self):
        checkFile = os.path.join(self.dataDir, 'fedoraus.xml')
        self.assert_(isinstance(checklist.CheckList(checkFile),
            checklist.CheckList))

    def test_ChecklistInvalidFile(self):
        self.assertRaises(error.InvalidChecklist, checklist.CheckList,
                os.path.join(self.dataDir, 'sample-save.xml'))

    def test_ChecklistNotAFile(self):
        self.assertRaises(error.InvalidChecklist, checklist.CheckList,
                'gobbledygook.xml')

    #
    # Treetip creation function
    #
    def test_TreetipCreateSuccess(self):
        self.assert_(isinstance(treetips.TreeTips(), treetips.TreeTips))

    def test50_TreetipCreateSuccessCheckView(self):
        view = checkview.CheckView()
        self.assert_(isinstance(treetips.TreeTips(view, 1), treetips.TreeTips))

    def test_TreetipCreateSuccessTreeView(self):
        view = gtk.TreeView()
        self.assert_(isinstance(treetips.TreeTips(view, 1), treetips.TreeTips))

    def test_TreetipCreateNotATreeView(self):
        self.assertRaises(TypeError, treetips.TreeTips, 3, 1)

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
