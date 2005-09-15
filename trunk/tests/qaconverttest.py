#!/usr/bin/python -tt
# File: qaconverttest.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 14 Sept 2005
# Copyright: Toshio Kuratomi
# License: GPL
# $Id$
'''Tests that the qaconvert script properly converts from qasave-0.1 to
checklist-0.3 format.
'''
__revision__ = '$Rev$'

import os
import sys
import unittest
import tempfile

import test

import checklist

class TestCreation(unittest.TestCase):
    def setUp(self):
        self.newList = None
        self.dataDir = os.path.abspath(os.path.join(test.srcdir, '..', 'data'))
        self.tempDir = tempfile.mkdtemp()
        self.checkFile = os.path.join(self.tempDir, 'new.save')
        for filename in os.listdir(self.dataDir):
            os.symlink(os.path.join(self.dataDir, filename),
                    os.path.join(self.tempDir, filename))

    def tearDown(self):
        for filename in os.listdir(self.tempDir):
            os.remove(os.path.join(self.tempDir, filename))
        os.removedirs(self.tempDir)

    def run_qa_convert(self, savefile):
        os.system('python %s %s %s &>/dev/null' %
                (os.path.join('..', 'src', 'qa-convert'),
                    os.path.join('qasave-0.1', savefile),
                    self.checkFile))
        #try:
        self.newList = checklist.CheckList(self.checkFile)
        #except:
            # If the checklist raises and exception, let the assert_ catch the
            # error.
        #    pass
        self.assert_(isinstance(self.newList, checklist.CheckList))
   
    #
    # Check that vaious invocations of qa-convert yield correct results.
    #
    def test_custom_items(self):
        '''Check conversion with custom items
        '''
        self.run_qa_convert('customitems.save')
   
    def test_many_changes(self):
        '''Check conversion with many changes
        '''
        self.run_qa_convert('ddclient.save')

    def test_few_changes(self):
        '''Check conversion with few changes
        '''
        self.run_qa_convert('pyrex.save')

    def test_some_changes(self):
        '''Check conversion with a moderate number of changes
        '''
        self.run_qa_convert('python-docutils.save')

def suite():
    otherPriority = unittest.makeSuite(TestCreation, 'test_')
    return unittest.TestSuite((otherPriority))

if __name__ == '__main__':
    suite = suite()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)
