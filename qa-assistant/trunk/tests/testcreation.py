# File: testcreation.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 24 Sept 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
'''Tests creation of all teh objects in QA Assistant.
'''
__version__ = '0.1'
__revision__ = '$Rev$'

import os
import unittest

import error
import checklist

class TestCreation(unittest.TestCase):
    def setUp(self):
        self.dataDir = os.path.join(os.environ['srcdir'], '..', 'data')

    def testChecklistCreateSuccess(self):
        self.assert_(str(type(checklist.CheckList(os.path.join(
            self.dataDir, 'fedoraus.xml'))))
            == "<class 'checklist.CheckList'>")

    def testChecklistInvalidFile(self):
        self.assertRaises(error.InvalidChecklist, checklist.CheckList,
                os.path.join(self.dataDir, 'sample-save.xml'))

    def testChecklistNotAFile(self):
        self.assertRaises(error.InvalidChecklist, checklist.CheckList,
            'gobbledygook.xml')

    def suite(self):
        return unittest.makeSuite(TestCreation,'test')

if __name__ == '__main__':
    suiteCreation = unittest.makeSuite(TestCreation, 'test')
    unittest.TextTestRunner(verbosity=2).run(suiteCreation)
