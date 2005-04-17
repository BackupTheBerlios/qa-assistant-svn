# File: properties.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 22 January 2005
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
'''A class that holds properties on a checklist file.'''
__revision__ = "$Rev$"

class PropEntry(object):
    '''Hold information on properties.
    
    Attributes:
    :propType: The type of property.  One of optional, onload, or automatic
    :value: The value of the property.
    :valueType: The type of the value.
    :function: A function that may be used to set the property.
    :args: List of other properties to use as arguments to the property
           setting function.

    Example:
    entry = PropEntry()
    entry.value = 'http://localhost/fc3/repo/foo-1.0-1.src.rpm'
    entry.valueType = 'url'
    entry.propType = 'onload'
    entry.function = 'srpm_from_ticket'
    entry.functionType = 'propset'
    entry.args = ['ticketURL',]
    props = Properties()
    props['SRPMfile'] = entry
    
    '''
    __slots__ = ('value', 'valueType', 'propType', 'function',
            'functionType', 'args')

    def __init__(self):
        self.value = None
        self.valueType = None
        self.propType = None
        self.function = None
        self.functionType = None
        self.args = []

class Properties(dict):
    ''' Holds the CheckList Properties.
        
    Every CheckList may have information about the object that it is reviewing.
    '''

    def __init__(self):
        '''Create a new Properties object.
        '''
        dict.__init__(self)
        self._sortedKeys = []
        self._requirementsMet = False
        
    #
    # Set Property values
    #

    ### FIXME: two things are not yet implemented:
    # 1) Functions are invoked somehow when entries are changed.
    # 2) Have checks that verify that a given type is correct:
    #    (int, URL, etc)
    def __setitem__(self, key, value):
        '''Set a property to a value.

        Override the default method so that we create new values when
        passed an entire PropEntry.  If we are only passed a value for the
        PropEntry, set the indicated Property's value if it exists.
        If it doesn't exist, and you want to be able to set it, you need to
        first add it by passing in a complete PropEntry struct.
        '''
        if isinstance(value, PropEntry):
            dict.__setitem__(self, key, value)
            self._sortedKeys.append(key)
        else:
            try:
                attrib = self[key]
            except KeyError:
                raise KeyError, (
                        'This checklist has no %s Property' % (key))
            attrib.value = value
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
