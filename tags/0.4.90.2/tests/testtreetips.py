#!/usr/bin/python -tt
# File: testtreetips.py
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

class TestTreeTips(unittest.TestCase):
    def setUp(self):
        self.model = gtk.TreeStore(gobject.TYPE_STRING)
        self.column = 0
        self.model.set(self.model.append(None), self.column, 'First entry')
        self.model.set(self.model.append(None), self.column, 'Second entry')
        self.view = gtk.TreeView(self.model)
        self.tt = treetips.TreeTips(self.view)

    def test_TreeTipsSetDelay(self):
        '''Setting the delay property to another value'''
        self.tt.set_property('delay', 1000)
        self.assertEqual(self.tt.get_property('delay'), 1000)
        self.tt.set_property('delay', 20)
        self.assertEqual(self.tt.get_property('delay'), 20)

    def test_EnableDisable(self):
        '''Enabling and disabling TreeTips.'''
        self.tt.disable()
        self.assertEqual(self.tt.get_property('enabled'), False)
        self.tt.enable()
        self.assertEqual(self.tt.get_property('enabled'), True)

    def test_ChangingColumn(self):
        '''Setting the column property'''
        self.tt.set_property('column', 3)
        self.assertEqual(self.tt.get_property('column'), 3)

    def test_ChangingView(self):
        '''Setting the view property'''
        view = gtk.TreeView(self.model)
        self.tt.set_property('view', view)
        self.assertEqual(self.tt.get_property('view'), view)

    def test_ChangingDelay(self):
        '''Setting the delay property'''
        self.tt.set_property('delay', 1001)
        self.assertEqual(self.tt.get_property('delay'), 1001)
        
    def test_TreeTipsReadOnlyProperties(self):
        '''Reading read-only treetip properties'''
        self.assert_(isinstance(self.tt.get_property('tip-window'), gtk.Window))
        self.assert_(isinstance(self.tt.get_property('tip-label'), gtk.Label))
        self.assert_(isinstance(self.tt.get_property('enabled'), BooleanType))
        self.assert_(isinstance(self.tt.get_property('active-tips-data'),
            StringType))


    def tearDown(self):
        del self.tt

def suite():
    otherPriority = unittest.makeSuite(TestTreeTips, 'test_')
    return otherPriority

if __name__ == '__main__':
    suite = suite()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)
