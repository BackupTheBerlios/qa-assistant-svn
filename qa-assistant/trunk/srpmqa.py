# File: srpmqa.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 15 April, 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
"""
"""
__revision__ = "$Rev$"

import gtk
from genericqa import GenericQA

class SRPMQA(GenericQA):

    def __init__(self, app):
        GenericQA.__init__(self, app)

        self.prepend(gtk.SeparatorMenuItem())

        bugzillaItem = gtk.MenuItem('From _Bugzilla')
        bugzillaItem.connect('activate', self.from_bugzilla_callback)
        self.prepend(bugzillaItem)
        
        srpmItem = gtk.MenuItem('From S_RPM')
        srpmItem.connect('activate', self.from_srpm_callback)
        self.prepend(srpmItem)

        submitItem = gtk.MenuItem('_Submit to Bugzilla')
        submitItem.connect('activate', self.submit_to_bugzilla_callback)
        self.append(submitItem)

    def from_srpm_callback(self, menuEntry):
        """Open a new review based on the user selected SRPM"""

        fileSelect = gtk.FileSelection(title='Select an SRPM to load')
        if (os.path.isdir(self.app.properties.lastSRPMDir) and
                os.access(self.app.properties.lastSRPMDir, os.R_OK|os.X_OK)):
            fileSelect.set_filename(self.app.properties.lastSRPMDir)

        fileSelect.hide_fileop_buttons()
        response = fileSelect.run()
        try:
            if response == gtk.RESPONSE_OK:
                filename = fileSelect.get_filename()
                self.app.properties.lastSRPMDir = os.path.dirname(filename)+'/'
                self.app.__SRPM_into_properties(filename)
        finally:
            fileSelect.destroy()
            del fileSelect

    def from_bugzilla_callback(self, menuEntry):
        """Open a new review with bugzilla report ID"""
        msg = """Associates this review with a bugzilla report.  The program needs to be able to use this to pick out information from a bugzilla report in order to autodownload packages and otherwise set up an environment for reviewing.  Although definitely cool, there's a good deal of work necessary for this to work.
        
Relative priority: Enhancement sometime after new review from SRPM. (Rather low)"""
        self.not_yet_implemented(msg)
        pass

    def submit_to_bugzilla_callback(self, menuEntry):
        """Submit a review to bugzilla."""
        msg = """Submits a review via Bugzilla XML-RPC.  Coolness factor, but Publish is a more important feature as it gives the user a greater ability to look review and modify the generated review.  When we get better editing features into the checklist this will be more important.
        
Relative Priority: Publish will be the primary submission for now.  This is an enhancement and should depend on having better editing of the review first."""
        self.app.not_yet_implemented(msg)
        pass
