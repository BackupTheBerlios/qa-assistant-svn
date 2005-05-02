# File: srpmqa.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 15 April, 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
"""
"""
__revision__ = "$Rev$"

### FIXME: Work some of these into the SRPM QA Process
# This is what the fedora startqa script does.
#Give bugzilla #
#finds URL to SRPM
#Finds md5sum URL
#Checks for local SRPM
#checks md5sum
#downloads source from spec URL
#offers you to view spec
#offers to build the rpm in mach
#read rpmlint's advice
#check files in binary package
#shows you report
#
#(Only appears to output a report on PUBLISH, not on NEEDSWORK)

import os

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
                self.app.SRPM_into_properties(filename)
        finally:
            fileSelect.destroy()
            del fileSelect

    def from_bugzilla_callback(self, menuEntry):
        """Open a new review with bugzilla report ID"""
        msg = """Associates this review with a bugzilla report.  The program needs to be able to use this to pick out information from a bugzilla report in order to autodownload packages and otherwise set up an environment for reviewing.  Although definitely cool, there's a good deal of work necessary for this to work.
        
Relative priority: Enhancement sometime after new review from SRPM. (Rather low)"""
        self.app.not_yet_implemented(msg)
        pass

    def submit_to_bugzilla_callback(self, menuEntry):
        """Submit a review to bugzilla."""
        msg = """Submits a review via Bugzilla XML-RPC.  Coolness factor, but Publish is a more important feature as it gives the user a greater ability to look review and modify the generated review.  When we get better editing features into the checklist this will be more important.
        
Relative Priority: Publish will be the primary submission for now.  This is an enhancement and should depend on having better editing of the review first."""
        self.app.not_yet_implemented(msg)
        pass

    ### FIXME: THis is copied here from the main qareviewer file.  It doesn't
    # belong here but this is becoming a holding ground for all SRPM related
    # functions until I have a chance to integrate them properly.
    def SRPM_into_properties(self, filename):
        '''Add an SRPM file into our properties structure.
        
        Keyword -- arguments:
        filename -- filename of the SRPM

        Sets our properties to use the specified SRPM file for the checklist.
        '''
        
        msg = 'Please select "QA Action => From SRPM"\nor "QA Action => From Bugzilla" to start the QA process.'
        self.lastSRPMDir = os.path.dirname(filename)+'/'
        try:
            self.properties.load_SRPM(filename)
        except Properties.FileError, message:
            self.startLabel.set_text("Unable to process that SRPM: %s\n%s" % (message.__str__(), msg))
        except Properties.SecurityError, message:
            ### FIXME: 
            # Set up a review based on the security error
            # Information needed from SRPM:
            # nice message suitable for sticking into a review
            # MD5Sum of file
            # Also -- there are two types of Security Errors right now:
            # SRPM problems and general unrpm problems related to race
            # conditions.  Need to separate:  SecurityError
            # MalFormedSRPMError
            # Dialog to display review and ask user if they want to publish
            # If user selects then publish it to file
            # [DIALOG]
            # PUBLISH -1
            # MD5Sum of src.rpm
            # Description of problem
            # [Publish] [Submit to Bugzilla] [Cancel]
            # [END DIALOG]
            # else allow user to select a new file
            #
            # Everything from here to pass is a hack and needs to go
            self.startLabel.set_text("SECURITY Error processing SRPM: %s" % (message))
            del self.properties.SRPM
            self.properties.SRPM = None
            pass

        self.__check_readiness()

        ### FIXME: Eventually properties should be a gobject and this
        # should be caught by a signal.connect in the Review Widget.
        # Moving it into the checklist
        #self.reviewView.update_hash()

    def __check_readiness(self):
        """Checks whether an SRPM is loaded or not.

        This should be called everytime property.SRPM changes.
        """
        
        if self.properties.SRPM:
            SRPMName = os.path.basename(self.properties.SRPM.filename)
            self.mainWinAppBar.pop()
            self.mainWinAppBar.push(SRPMName)
            self.ReviewerWindow.set_title(HUMANPROGRAMNAME + ' - ' +
                    SRPMName)
            self.startLabel.hide()
            self.listPane.show()
            self.grabBar.show()
            if self.grabArrow.get_property('arrow-type') == gtk.ARROW_RIGHT:
                self.reviewScroll.show()
        else:
            if self.grabArrow.get_property('arrow-type') == gtk.ARROW_RIGHT:
                self.reviewScroll.hide()
            self.grabBar.hide()
            self.listPane.hide()
            self.startLabel.show()
            self.ReviewerWindow.set_title(HUMANPROGRAMNAME)
            self.mainWinAppBar.pop()
            self.mainWinAppBar.push("No SRPM selected")

### FIXME: copied here from properties.py.  Being replaced.
import SRPM
class Properties(object):
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
