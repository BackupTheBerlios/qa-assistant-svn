# File: testchecklist.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 24 Sept 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$

import unittest
import re
import os

import checklist

class TestCheckList(unittest.TestCase):
    def setUp(self):
        self.checkFile = os.path.join(os.environ['srcdir'], '..', 'data',
                'fedoraus.xml')
        self.checklist = checklist.CheckList(self.checkFile)

    def testCheckListPangoize(self):
        outputRE = re.compile('^<span foreground="[^"]+">&lt;pseudo&gt;A little bit o\' this &amp; that&lt;/pseudo&gt;</span>$')
        out = self.checklist.pangoize_output('Fail', "<pseudo>A little bit o' this & that</pseudo>")

        self.assert_(outputRE.search(out), 'CheckList fails to escape output properly')

    def testCheckListUnpangoize(self):
        out = self.checklist.unpangoize_output('<span foreground="red">&lt;pseudo&gt;A little bit o\' this &amp; that&lt;/pseudo&gt;')
        self.assert_(out == '<pseudo>A little bit o\' this & that</pseudo>', 'CheckList fails to unescape output properly.')

    ### FIXME: test add_entry w/ valid and invalid
    # test publish()
    # test check_category_resolution(changedRow == iter, newValue of row)

    def tearDown(self):
        del self.checklist

    def suite(self):
        return unittest.makeSuite(TestCheckList,'test')

if __name__ == '__main__':
    suiteCheckList = unittest.makeSuite(TestCheckList, 'test')
    unittest.TextTestRunner(verbosity=2).run(suiteCheckList)
