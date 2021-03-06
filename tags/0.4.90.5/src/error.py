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
    
class InvalidResolution(Error):
    '''The resolution is not valid because it is not listed within the
       resolutionlist for the checklist item.
    '''
    pass
    
class InvalidChecklist(Error):
    '''The given checklist is invalid for some reason.'''
    pass
    
class CannotAccessFile(IOError):
    '''We were unable to access the given filename.'''
    pass
    
class InvalidFunctions(Error):
    '''The functions referenced from a checklist were invalid.'''
    pass
class UnknownHashType(Error):
    '''The specified hash is not one we're familiar with.'''
    pass

# GPG Exceptions
class GPGError(Error):
    '''An error generated by gpg.'''
    pass

class BadPassphrase(GPGError):
    '''Passphrase didn't work with GPG.'''
    pass

class NoSecretKey(GPGError):
    '''There was no secret key for the specified user id.'''
    pass

class NotGPGCompatible(GPGError):
    '''The program selected in the preferences isn't compatible with gpg.'''
    pass
    
class NoOut(GPGError):
    '''The signing did not generate any output.'''
    pass
