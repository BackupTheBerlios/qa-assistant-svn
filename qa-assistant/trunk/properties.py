#! /usr/bin/python
#
# File: properties.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 2 March, 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
"""A class that holds properties on a review file.
"""
__version__ = "0.1"
__revision__ = "$Revision$"

class Properties:
    def __init__(self, checklist, SRPM):
        """Create a new properties box."""

        ### FIXME: we really need to take this information from the user
        # instead of setting it here.  But I just want to get something
        # working right now.
        self.checklistName = checklist
        self.SRPM = SRPM
        # self.bugzillaURL
        # self.bugzillaNumber
        pass

    def dialog(self):
        """Popup a dialog allowing the user to edit the review's properties.
        
        """
        pass
