# File: error.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 25 August 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
'''
Exception classes for QA Assistant.
'''
__revision__ = '$Rev$'

class Error(Exception):
    '''Base class for Exceptions in QA Assistant.'''
    def __init__(self, msg):
        Exception.__init__(self, msg)
        self.msg = msg

class DuplicateItem(Error):
    '''An item duplicates a value already present in a checklist.'''
    pass
    
class InvalidChecklist(Error):
    '''The given checklist is invalid for some reason.'''
    pass
    
class CannotAccessFile(Error):
    '''We were unable to access the given filename.'''
    pass
