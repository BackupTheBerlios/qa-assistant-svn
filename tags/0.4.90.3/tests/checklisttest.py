#!/usr/bin/python -tt
# File: checklisttest.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 24 Sept 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$

import unittest
import re
import os
import sys

import test

import checklist
import error
import libxml2

class TestCheckList(unittest.TestCase):
    def setUp(self):
        self.checkFile = os.path.join(test.srcdir, '..', 'data',
                'fedoraus.xml')
        self.checklist = checklist.CheckList(self.checkFile)

    def tearDown(self):
        del self.checklist

    def test_CheckListPangoize(self):
        '''Escape output for pango usage

        Take a string with special characters and pass it through the checklist
        pangoize_output() function.  Be sure the output is properly escaped
        for use with pango.
        '''
        outputRE = re.compile('^<span foreground="[^"]+">&lt;pseudo&gt;A little bit o\' this &amp; that&lt;/pseudo&gt;</span>$')
        out = self.checklist.pangoize_output('Fail', "<pseudo>A little bit o' this & that</pseudo>")

        self.assert_(outputRE.search(out), 'CheckList fails to escape output properly')

    def test_0CheckListUnpangoize(self):
        '''Remove pango escaping

        Take a string with pango escape sequences and pass it through the
        checklist unpangoize_output() function.  Be sure the output has been
        converted into the equivalent human readable string.
        '''
        out = self.checklist.unpangoize_output('<span foreground="red">&lt;pseudo&gt;A little bit o\' this &amp; that&lt;/pseudo&gt;')
        self.assert_(out == '<pseudo>A little bit o\' this & that</pseudo>', 'CheckList fails to unescape output properly.')

    def test_CheckListAddEntry(self):
        '''Add more than one entry

        Add an entry and see if it added.  Add a second one and make sure
        that was added as well.  The first one creates a Custom Category in
        addition to creating the entry.  The second one merely adds to the
        now existent Custom Category.
        '''
        self.failIf(self.checklist.entries.has_key("custom checklist items"),
                'FAIL: Checklist already has a custom items category.')
        self.checklist.add_entry("This is a first test")
        self.assert_(self.checklist.entries.has_key("custom checklist items"),
                'FAIL: Did not create the Custom Checklist Items category')
        self.assert_(self.checklist.entries.has_key("this is a first test"),
                'FAIL: Did not create the first item')
        self.checklist.add_entry("This is a second test")
        self.assert_(self.checklist.entries.has_key("this is a second test"),
                'FAIL: Did not create the second item')

    def test_CheckListAddEntryDefaultsValuesOk(self):
        '''Default values are set for the checklist
        
        Add an entry to the checklist with all default values.  Check that the
        default values are what is documented.
        '''
        outList = {'Needs-Reviewing' : '',
                   'Pass' : '',
                   'Fail' : '',
                   'Non-Blocker' : '',
                   'Not-Applicable' : ''}
        self.checklist.add_entry("This is a first test")
        self.assert_(self.checklist.entries.has_key('this is a first test'),
                'FAIL: Entry was not added with default values')
        entry = self.checklist.entries['this is a first test']
        self.assert_(self.checklist.get_value(entry, checklist.ISITEM) == True,
                'FAIL: Checklist was not set to the default')
        self.assert_(self.checklist.get_value(entry, checklist.RESLIST) ==
                ['Needs-Reviewing', 'Pass', 'Fail', 'Non-Blocker', 'Not-Applicable'],
                'FAIL: Checklist resolution list was not set to the default')
        self.assert_(self.checklist.get_value(entry, checklist.SUMMARY) ==
                'This is a first test',
                'FAIL: Checklist summary was not set to the summary')
        self.assert_(self.checklist.get_value(entry, checklist.DESC) == None,
                'FAIL: Checklist description was not set to the default')
        self.assert_(self.checklist.get_value(entry, checklist.RESOLUTION) ==
                'Needs-Reviewing',
                'FAIL: Checklist resolution was not set to the default')
        self.assert_(self.checklist.unpangoize_output(
            self.checklist.get_value(entry, checklist.OUTPUT)) == '',
                'FAIL: Output was not set to the default')
        self.assert_(self.checklist.get_value(entry, checklist.OUTPUTLIST) ==
                outList,
                'FAIL: Outputlist was not set to default')
        self.assert_(self.checklist.get_value(entry, checklist.TEST) == None,
            'FAIL: Checklist test was not set to default')
        
    def test_CheckListAddEntryExplicit(self):
        '''Add entry with explicit values

        Add an entry to the checklist with explicit values.  Check that the
        values were correctly put into the data structure.
        '''
        resList = ['Guess', 'Me', 'Afterall']
        outList = {'Guess' : 'This is a guess',
                   'Me' : 'This is for entry Me',
                   'Afterall' : 'And something for afterall'}
        self.checklist.add_entry("This is a first test", item=True,
                display=True, resolution=resList[2],
                output=outList['Afterall'],
                outputList=outList,
                resList = resList, desc = 'This is a test entry')
        self.assert_(self.checklist.entries.has_key("this is a first test"),
                'FAIL: Did not add the item with explicit values.')
        entry = self.checklist.entries['this is a first test']
        self.assert_(self.checklist.get_value(entry, checklist.ISITEM) == True,
                'FAIL: Checklist was not set to be an item')
        self.assert_(self.checklist.get_value(entry, checklist.RESLIST) ==
                resList,
                'FAIL: Checklist resolution list was not set to given list')
        self.assert_(self.checklist.get_value(entry, checklist.SUMMARY) ==
                'This is a first test',
                'FAIL: Checklist summary was not set to the summary')
        self.assert_(self.checklist.get_value(entry, checklist.DESC) ==
                'This is a test entry',
                'FAIL: Checklist description was not set to the given description')
        self.assert_(self.checklist.get_value(entry, checklist.RESOLUTION) ==
                resList[2],
                'FAIL: Checklist resolution was not set to the given resolution')
        self.assert_(self.checklist.unpangoize_output(
            self.checklist.get_value(entry, checklist.OUTPUT)) ==
                outList["Afterall"],
                'FAIL: Output was not set to the given output')
        self.assert_(self.checklist.get_value(entry, checklist.OUTPUTLIST) ==
                outList,
                'FAIL: Outputlist was not set to default')
        self.assert_(self.checklist.get_value(entry, checklist.TEST) == None,
            'FAIL: Checklist test was not set to default')

    def test_CheckListAddEntryInvalidRes(self):
        '''Catch adding an entry with an invalid resolution

        Attempt to add an entry with a resolution that is not in the
        resolution list.  This should raise an InvalidResolution exception.
        '''
        self.assertRaises(error.InvalidResolution,
                self.checklist.add_entry, "This is a first test",
                    resolution="NotMe")
        self.assertRaises(error.InvalidResolution,
                self.checklist.add_entry, "This is a second test",
            resList=["True", "False", "Miss"],
            resolution="NotMe")

    def test_CheckListAddEntryDuplicateItem(self):
        '''Catch adding a duplicate item

        Attempt to add an item with the same Summary as another item.  This
        should raise a DuplicateItem exception.
        '''
        self.checklist.add_entry("This is a first test")
        self.assertRaises(error.DuplicateItem,
            self.checklist.add_entry, "THIS IS A FIRST TEST")
    
    def test_CheckListAddEntryIncompleteOutputList(self):
        '''Add entry with an outputlist shorter than the resolution list

        Add an entry that has an outputlist shorter than the resolution list.
        In this case, we should add the extra entries to the outputlist with
        default values.
        '''
        self.checklist.add_entry("This is a first test",
                outputList={'Thistle':'An output'},
                resList=['Not','Thistle', 'Here','Either'])
        entryIter = self.checklist.entries["this is a first test"]
        outList = self.checklist.get_value(entryIter, checklist.OUTPUTLIST)
        self.assert_(outList == {'Thistle': 'An output', 'Not': '', 'Here': '', 'Either': ''})

    ### FIXME: 
    # test publish() -> We can test that output matches input.  Or after we
    #   make some changes (add_entry/set)
    # test set()
    # test check_category_resolution(changedRow == iter, newValue of row)

    
class TestCheckListCreation(unittest.TestCase):
    '''Test Creation of CheckList objects.'''
    def setUp(self):
        libxml2.debugMemory(1)
        self.dataDir = os.path.join(test.srcdir, '..', 'data')

    def tearDown(self):
        libxml2.debugMemory(0)

    def test_0CheckListCreateSuccess(self):
        '''Create a CheckList

        Create a checklist.  Make sure the returned object is a CheckList.
        '''
        checkFile = os.path.join(self.dataDir, 'fedoraus.xml')
        self.assert_(isinstance(checklist.CheckList(checkFile),
            checklist.CheckList))

    def test_CheckListInvalidFile(self):
        '''Catch creating a CheckList with a non-CheckList file
        
        Try to create a CheckList with a non-CheckList xml file.  Make sure
        we raise an InvalidCheckList exception.
        '''
        self.assertRaises(error.InvalidChecklist, checklist.CheckList,
                os.path.join(self.dataDir, 'sample-save.xml'))

    def test_CheckListNotAFile(self):
        '''Catch creating a CheckList with a non-existant file

        Try to create a checklist with a non-existent file.  Make sure
        we raise an InvalidCheckList exception.
        '''
        self.assertRaises(error.InvalidChecklist, checklist.CheckList,
                'gobbledygook.xml')

    def test_CheckListCreateMemoryTest(self):
        '''Create a checklist with no memory leaks

        libxml2 requires special memory handling.  Check that we can create a
        CheckList and destory it without any memory leaks from the libxml2
        library.
        '''
        self.checklist = checklist.CheckList(os.path.join(self.dataDir,
            'fedoraus.xml'))
        libxml2.cleanupParser()
        self.assert_(libxml2.debugMemory(1) == 0,
                'FAIL: %d bytes leaked' % (libxml2.debugMemory(1)))
        del self.checklist

def suite():
    creationSuite = unittest.makeSuite(TestCheckListCreation, 'test_')
    runSuite = unittest.makeSuite(TestCheckList, 'test_')
    return unittest.TestSuite((creationSuite, runSuite))

if __name__ == '__main__':
    suite = suite()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)
