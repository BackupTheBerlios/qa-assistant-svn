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
    pass
    
class duplicateItem(Error):
    '''An item duplicates a value already present.'''
    pass
    
class invalidChecklist(Error):
    '''The given checklist is invalid for some reason.'''
    pass
