# File: properties.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 22 January 2005
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
'''A class that holds properties on a checklist file.'''
__revision__ = "$Rev$"

import gobject
import UserDict

class PropEntry(object):
    '''Hold information on properties.
    
    Attributes:
    :propType: The type of property.  One of optional, onload, or automatic
    :value: The value of the property.
    :valueType: The type of the value.
    :functions: A list of functions to be invoked when the PropEntry is set.

    Example:
    entry = PropEntry()
    entry.value = 'http://localhost/fc3/repo/foo-1.0-1.src.rpm'
    entry.valueType = 'url'
    entry.propType = 'onload'
    entry.functions = ('srpm_from_ticket',)
    props = Properties()
    props['SRPMfile'] = entry
    
    '''
    __slots__ = ('value', 'valueType', 'propType', 'functions')

    def __init__(self):
        self.value = None
        self.valueType = None
        self.propType = None
        self.functions = []

class Properties(gobject.GObject, UserDict.DictMixin):
    ''' Holds the CheckList Properties.
        
    Every CheckList may have information about the object that it is reviewing.
    '''

    __gsignals__ = {
        'changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                (gobject.TYPE_PYOBJECT,))
    }

    def __init__(self, functions):
        '''Create a new Properties object.
        '''
        gobject.GObject.__init__(self)
        self.storage = {}
        self._sortedKeys = []
        self._requirementsMet = False
        self.functions = functions
        
    #
    # Set Property values
    #

    ### FIXME: Not yet implemented:
    # 1) Have checks that verify that a given type is correct:
    #    (int, URL, etc)

    def __setitem__(self, key, value):
        '''Set a property to a value.

        Override the default method so that we can do these special things:
        1) create new values when passed an entire PropEntry.
        2) If we are only passed a value for the PropEntry, set the
           indicated Property's value if it exists.
           (If it doesn't exist, and you want to be able to set it, you need
            to first add it by passing in a complete PropEntry struct.)
        3) When a property is set, check if there are any functions that need
           to be called when that happens.
        '''
        if isinstance(value, PropEntry):
            self.storage[key] = value
            self._sortedKeys.append(key)
        else:
            try:
                attrib = self[key]
            except KeyError:
                raise KeyError, (
                        'This checklist has no %s Property' % (key))
            attrib.value = value

        # Let everyone know a property has changed
        self.emit('changed', key)
        # If the property has a function attached to it, run it.
        if self[key].functions:
            for function in self[key].functions:
                exec('self.functions.' + function + '()')

        # Check whether the properties have been completely filled out
        if self._requirementsMet and self[key].propType == 'onload' and not (
                self[key].value or self[key].value == 0):
            self._requirementsMet = False

    def keys(self):
        '''Return a sorted list of keys.

        We keep the list of keys in the order that they were entered into the
        array.  This gives the checklist author the ability to redefine the
        order in which properties are displayed to the user.
        '''
        return self._sortedKeys

    def _requires(self):
        '''Tell us if all the properties that need entering have been.
        '''
        if self._requirementsMet:
            return True
        for prop in self.keys():
            if self[prop].propType == 'onload' and not (self[prop].value
                    or self[prop].value == 0):
                return False
        self._requirementsMet = True
        return True

    requirementsMet = property(_requires,
            doc = '''Whether required properties been filled in''')

    def __delitem__(self, key):
        index = self._sortedKeys.index(key)
        del self._sortedKeys[index]
        return self.storage.__delitem__(key)
    
    # Functions to emulate a dict type.  gobject.GObject is not
    # multiply inheritable with dict so emulate the hard way.
    def __getitem__(self, key):
        return self.storage[key]

    def __contains__(self, *extras):
        return self.storage.__contains__(*extras)

    def __iter__(self):
        return self.storage.__iter__()
    
    def iteritems(self):
        return self.storage.iteritems()

    def has_key(self, *extras):
        return self.storage.has_key(*extras)

    def __repr__(self, *extras):
        return self.storage.__repr__(*extras)
gobject.type_register(Properties)
