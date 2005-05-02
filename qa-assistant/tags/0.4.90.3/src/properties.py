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
        self.__sortedKeys = []
    
    #
    # Set Property values
    #

    ### FIXME: two things are not yet implemented:
    # 1) Functions are invoked somehow when entries are changed.
    # 2) Have checks that verify that a given type is correct:
    #    (int, URL, etc)
    def __setitem__(self, key, value):
        '''Set a property to a value.

        Override the default method so that we only set the property if it
        already exists.  If it doesn't exist, and you want to be able to set
        it, you need to first add it via the add method.
        '''
        if isinstance(value, PropEntry):
            dict.__setitem__(self, key, value)
            self.__sortedKeys.append(key)
        else:
            try:
                attrib = self[key]
            except KeyError:
                raise KeyError, (
                        'This checklist has no %s Property' % (key))
            attrib.value = value

    def keys(self):
        '''Return a sorted list of keys.

        We keep the list of keys in the order that they were entered into the
        array.  This gives the checklist author the ability to redefine the
        order in which properties are displayed to the user.
        '''
        return self.__sortedKeys
