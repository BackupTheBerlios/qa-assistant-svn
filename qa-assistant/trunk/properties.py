# File: properties.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 2 March, 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
"""A class that holds properties on a review file.
"""
__revision__ = "$Rev$"

import sys

import SRPM

class Properties:
    class SecurityError(SRPM.SecurityError):
        pass
    class FileError(SRPM.FileError):
        pass

    def __init__(self):
        """Create a new properties box."""

        ### FIXME: we really need to take this information from the user
        # instead of setting it here.  But I just want to get something
        # working right now.
        self.SRPM = None

        ### FIXME: The following need to go into preferences (GConf)
        # Directories last searched (for FileSelect Dialogs)
        self.lastSRPMDir = './'
        self.lastSaveFileDir = './'
        self.lastReviewDir = './'
        # Colors to use on output text
        self.failColor = 'red'
        self.minorColor = 'purple'
        self.passColor = 'dark green'
        pass

    def dialog(self):
        """Popup a dialog allowing the user to edit the review's properties.
        
        """
        pass

    def load_SRPM(self, filename):
        """Given the SRPM's filename, attempt to open a review based on it.
        
        Keyword -- arguments:
            filename -- SRPM filename.
        
        Creates an SRPM object from the filename and saves it in self.SRPM.
        If there is a security problem with the SRPM, then save a SECURITY
        notice into a special security review property.  If there is a
        non-security problem, raise the exception.
        """
        try:
            self.SRPM = SRPM.SRPM(filename)
        # Pass these through to the calling program as Property exceptions
        # rather than SRPM exceptions
        except SRPM.FileError, message:
            self.SRPM = None
            raise self.FileError(message.__str__())
        except SRPM.SecurityError:
            excName, exc = sys.exc_info()[:2]
            raise self.SecurityError, (exc.id, exc.filename, exc.message)

    def set(name, property):
        """Set a property from the program. """
        if hasattr(name):
            setattr(name, property)
        else:
            raise AttributeError (1)
