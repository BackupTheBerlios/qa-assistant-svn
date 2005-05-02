#!/usr/bin/python -tt
# File: propertiestest.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 19 Feb 2005
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$

import unittest
import os
import sys

from types import *

import test

import properties

class TestPropEntry(unittest.TestCase):
    def setUp(self):
        self.propEntry = properties.PropEntry()
        
    def tearDown(self):
        del self.propEntry
        
    def test_PropEntryInvalidAttribute(self):
        '''Catch adding an invalid value

        Attempt to add an invalid attribute to the PropEntry.  This should
        raise an AttributeError.
        '''
        try:
            self.propEntry.invalid = 5
        except AttributeError:
            self.assert_(True)
        else:
            self.assert_(False)

    def test_PropEntrySetAttributes(self):
        '''Set legal attributes on PropEntry

        Attempt to set values on all PropEntry's legal attributes.
        '''
        value = 'http://localhost/fc3/repo/foo-1.0-1.src.rpm'
        valueType = 'url'
        propType = 'onload'
        function = 'srpm_from_ticket'
        args = ('ticketURL')

        try:
            self.propEntry.value = value
            self.propEntry.valueType = valueType
            self.propEntry.propType = propType
            self.propEntry.function = function
            self.propEntry.args = args
        except:
            self.assert_(False,
                    'FAIL: PropEntry  would not set a legal attribute')
        self.assert_(self.propEntry.value == value,
                'FAIL: PropEntry.value was not set to the given value')
        self.assert_(self.propEntry.valueType == valueType,
                'FAIL: PropEntry.valueType was not set to the given value')
        self.assert_(self.propEntry.propType == propType,
                'FAIL: PropEntry.propType was not set to the given value')
        self.assert_(self.propEntry.function == function,
                'FAIL: PropEntry.function was not set to the given value')
        self.assert_(self.propEntry.args == args,
                'FAIL: PropEntry.args was not set to the given value')
        
class TestPropertiesCreation(unittest.TestCase):
    def test_CreateProperties(self):
        '''Create a Properties object

        Make sure creating a properties structure works.
        '''
        self.assert_(isinstance(properties.Properties(), properties.Properties))
            
class TestProperties(unittest.TestCase):
    def setUp(self):
        # Create a property Entry to add to the checklist
        self.value = 'http://localhost/fc3/repo/foo-1.0-1.src.rpm'
        self.valueType = 'url'
        self.propType = 'onload'
        self.function = 'srpm_from_ticket'
        self.args = ('ticketURL')
        self.name = 'SRPMURL'
        self.propEntry = properties.PropEntry()
        self.propEntry.value = self.value
        self.propEntry.valueType = self.valueType
        self.propEntry.propType = self.propType
        self.propEntry.function = self.function
        self.propEntry.args = self.args
        self.prop = properties.Properties()
        self.prop[self.name] = self.propEntry

    def test_50AddProperty(self):
        '''Add a property Entry to the Properties object
        
        Test whether adding a PropEntry to a Properties object will succeed
        in being added.
        '''
        self.assert_(isinstance(self.prop[self.name], properties.PropEntry),
                'FAIL: Did not store the PropEntry into the Properties object')
        self.assert_(self.prop[self.name].value == self.value,
                'FAIL: Did not set the Properties value correctly')
        self.assert_(self.prop[self.name].valueType == self.valueType,
                'FAIL: Did not set the Properties valueType correctly')
        self.assert_(self.prop[self.name].propType == self.propType,
                'FAIL: Did not set the Properties propType correctly')
        self.assert_(self.prop[self.name].function == self.function,
                'FAIL: Did not set the Properties function correctly')
        self.assert_(self.prop[self.name].args == self.args,
                'FAIL: Did not set the Properties args correctly')

    def test_PropertiesChangeValue(self):
        '''Change a value on a property

        Create a property.  Then test whether we can change the value.
        '''

        newValue = 'http://localhost/test/bar-1.0-1.src.rpm'
        self.prop[self.name] = newValue
        self.assert_(self.prop[self.name].value == newValue)

    def test_PropertiesInvalidChange(self):
        '''Catch changing the value of an entry that hasn't been added

        Test whether we correctly refuse to set a value when we haven't
        entered a PropEntry for it yet.
        '''
        newValue = 'http://localhost/test/bas-1.0-1.src.rpm'
        self.assertRaises(KeyError, self.prop.__setitem__,
                'Invalid', newValue)

    def test_PropertiesKeyOrder(self):
        '''Check Properties stores keys in FIFO order.

        Test that we can add PropEntries to the Properties object and retrieve
        the keys for the objects in the same order we put them in.
        '''
        for i in ('one', 'two', 'three'):
            propEntry = properties.PropEntry()
            propEntry.valueType = 'string'
            propEntry.propType = 'optional'
            self.prop[i] = propEntry
    
        self.assert_(self.prop.keys() == [self.name, 'one', 'two', 'three'])

    def tearDown(self):
        pass

def suite():
    entrySuite = unittest.makeSuite(TestPropEntry, 'test_')
    createPropSuite = unittest.makeSuite(TestPropertiesCreation, 'test_')
    propertiesSuite = unittest.makeSuite(TestProperties, 'test_')
    return unittest.TestSuite((entrySuite, createPropSuite, propertiesSuite))

if __name__ == '__main__':
    suite = suite()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)
