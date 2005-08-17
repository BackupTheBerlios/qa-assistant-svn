#!/usr/bin/python -tt
# File: treetipstest.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 3 Oct 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$

import unittest
import os
import sys
import gtk
import gobject

from types import *

import test

import treetips

try:
    import checkview
except ImportError:
    haveCheckView = False
else:
    haveCheckView = True

class TestTreeTipCreation(unittest.TestCase):
    '''Test that TreeTips are correctly created.'''
    def test_TreetipCreateSuccess(self):
        '''Create TreeTips without any TreeView set

        Create an empty treetips that doesn't point to anything.   
        '''
        self.assert_(isinstance(treetips.TreeTips(), treetips.TreeTips))

    def testOptional_TreetipCreateSuccessCheckView(self):
        '''Create TreeTips with a CheckView data source

        Create a TreeTips object that references a CheckView as its data
        source.
        '''
        view = checkview.CheckView()
        self.assert_(isinstance(treetips.TreeTips(view, 1), treetips.TreeTips))

    def test_TreetipCreateSuccessTreeView(self):
        '''Create TreeTips with TreeView data soruce

        Create a TreeTips object that references a standard gtk.TreeView to
        get its information.
        '''
        view = gtk.TreeView()
        self.assert_(isinstance(treetips.TreeTips(view, 1), treetips.TreeTips))

    def test_TreetipCreateInvalidTreeView(self):
        '''Catch trying to create a TreeTips with a non-TreeView object

        Attempt to create a TreeTips with an integer instead of a gtk.TreeView
        and make sure we raise a TypeError when this happens.
        '''
        self.assertRaises(TypeError, treetips.TreeTips, 3, 1)

class TestTreeTips(unittest.TestCase):
    def setUp(self):
        self.model = gtk.TreeStore(gobject.TYPE_STRING)
        self.column = 0
        self.model.set(self.model.append(None), self.column, 'First entry')
        self.model.set(self.model.append(None), self.column, 'Second entry')
        self.view = gtk.TreeView(self.model)
        self.tt = treetips.TreeTips(self.view)

    def tearDown(self):
        del self.tt

    def test_TreeTipsSetDelay(self):
        '''Set the delay property to another value
        
        Test that we can set the delay property on the TreeTips.
        '''
        self.tt.set_property('delay', 1000)
        self.assertEqual(self.tt.get_property('delay'), 1000)
        self.tt.set_property('delay', 20)
        self.assertEqual(self.tt.get_property('delay'), 20)

    def test_EnableDisable(self):
        '''Enable and disable TreeTips
        
        Toggle the treetips on and off by setting and unsetting the
        TreeTips disable property.
        '''
        self.tt.disable()
        self.assertEqual(self.tt.get_property('enabled'), False)
        self.tt.enable()
        self.assertEqual(self.tt.get_property('enabled'), True)

    def test_ChangingColumn(self):
        '''Set the column of the TreeView the TreeTips use
        
        Change the TreeView column the TreeTips get their column from.
        '''
        self.tt.set_property('column', 3)
        self.assertEqual(self.tt.get_property('column'), 3)

    def test_ChangingView(self):
        '''Set the view property
        
        Change the TreeView that the TreeTips use to get their tip information.
        '''
        view = gtk.TreeView(self.model)
        self.tt.set_property('view', view)
        self.assertEqual(self.tt.get_property('view'), view)

    def test_ChangingDelay(self):
        '''Set the delay property
        
        Change the delay property to something else.
        '''
        self.tt.set_property('delay', 1001)
        self.assertEqual(self.tt.get_property('delay'), 1001)
        
    def test_TreeTipsReadOnlyProperties(self):
        '''Read read-only treetip properties
        
        Check that we can read from all the supported TreeTip properties.
        '''
        self.assert_(isinstance(self.tt.get_property('tip-window'), gtk.Window))
        self.assert_(isinstance(self.tt.get_property('tip-label'), gtk.Label))
        self.assert_(isinstance(self.tt.get_property('enabled'), BooleanType))
        self.assert_(isinstance(self.tt.get_property('active-tips-data'),
            StringType))


def suite():
    createTreeTips = unittest.makeSuite(TestTreeTipCreation, 'test_')
    treeTipsSuite = unittest.makeSuite(TestTreeTips, 'test_')
    if haveCheckView == True:
        optTreeTips = unittest.makeSuite(TestTreeTipCreation, 'testOptional_')
        return unittest.TestSuite((createTreeTips, optTreeTips, treeTipsSuite))
    else:
        return unittest.TestSuite((createTreeTips, treeTipsSuite))

if __name__ == '__main__':
    suite = suite()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)
