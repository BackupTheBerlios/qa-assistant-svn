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

from types import *

import test

import treetips

class TestTreeTips(unittest.TestCase):
    def setUp(self):
        self.tt = treetips.TreeTips()

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

    def test_TreeTipsReadOnlyProperties(self):
        '''Reading read-only treetip properties'''
        self.assert_(isinstance(self.tt.get_property('tip_window'), gtk.Window))
        self.assert_(isinstance(self.tt.get_property('tip_label'), gtk.Label))
        self.assert_(isinstance(self.tt.get_property('enabled'), BooleanType))

    ### FIXME:
    # Test properties: view, column,
    # functions enable, disable

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
