# File: qareviewer.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 4 Mar 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Description: Main QAReviewer application object
# Id: $Id$
"""QA Reviewer object.

The main program object.  From here we set up the user interface, receive
events, and send things off for future processing.
"""
__revision__ = "$Rev$"

import sys
import os
import libxml2
import gtk
import gtk.glade
import gnome

from qaconst import *
import gnomeglade
import error
import checkload
from review import Review
from checklist import CheckList
from checkview import CheckView
from preferences import Preferences

__version__ = VERSION

class QAReviewer(gnomeglade.GnomeApp):
    '''Main Program Object.

    '''
    def __init__(self, arguments):
        """Creates a new QA reviewer window.
           
        Keyword -- arguments:
        arguments: A commandline to process when setting up the environment
        """
        # Load the interface
        gladefile = 'glade/qa-assistant.glade'
        gnomeglade.GnomeApp.__init__(self, PROGRAMNAME, __version__,
                gladefile, 'ReviewerWindow')
        self.program.set_property(gnome.PARAM_HUMAN_READABLE_NAME,
                HUMANPROGRAMNAME)
       
        #
        # Create additional interface components
        #

        iconFile = gnomeglade.uninstalled_file('pixmaps/qa-icon.png')
        if iconFile == None:
            iconFile = self.locate_file(gnome.FILE_DOMAIN_APP_PIXMAP,
                                        'qa-icon.png')
            if iconFile == []:
                iconFile = None
            else:
                iconFile = iconFile[0]
        if iconFile:
            self.logo = gnomeglade.load_pixbuf(iconFile)
            self.ReviewerWindow.set_property('icon', self.logo)

        # Create the views onto the checklist
        self.checkView = CheckView()
        self.listPane.add(self.checkView)
        self.reviewView = Review()
        self.reviewPane.add(self.reviewView)

        self.grabArrow=gtk.Arrow(gtk.ARROW_LEFT, gtk.SHADOW_NONE)
        self.grabArrow.set_size_request(4,4)
        label=self.grabBar.get_child()
        self.grabBar.remove(label)
        self.grabBar.add(self.grabArrow)
        self.grabArrow.show()

        self.reviewScroll.hide()

        # Create our Clipboard
        self.clipboard = gtk.Clipboard(gtk.gdk.display_get_default(),
                'CLIPBOARD')
        self.clipPrimary = gtk.Clipboard(gtk.gdk.display_get_default(),
                'PRIMARY')

        # Set default paths for File Dialogs to look in
        self.lastSRPMDir = './'
        self.lastSaveFileDir = './'
        self.lastReviewDir = './'

        #
        # Command line initialization
        #

        self.checklist = None
        ### FIXME: Read commandline for things like a checklist file specified.
        # If there is a checklist on the commandline, send it to the druid to
        # be loaded.
        # load that.  The
        # properties tell us if there's any information that must be taken
        # from the user.  Or if it's already been filled out.

        #
        # Blast off!
        #
        
        if self.checklist:
            ### FIXME: Decide if there's additional properties that must be
            # filled out.
            self.ReviewerWindow.show()
        else:
            ### FIXME: While the Druid is onscreen, set everything in the
            # ReviewerWindow to be insensitive.
            # If no checklist is loaded, only file::New and file::Load should
            # work.... (?)
            startDruid = checkload.NewDruid(self, checkload.START)
            startDruid.set_icon(self.logo)
            startDruid.show_all()
            ### FIXME: Note that the druid must destroy itself when it is
            # finished.
            # If there's no checklist on the commandline, popup the Druid that
            # asks the user to select a checklist from the installed defaults
            # or a savefile.  (Same type of file, but they have distinctly
            # different needs in terms of selecting.
            # CheckLists will all be located someplace in the system that the
            # program knows about.  so a simple selector can be used.
            # savefiles will be inplaces that the user knows about (maybe in the
            # home directory or in the CWD.)  So the user should get a file
            # selector for this.
            #
            # Once the user selects a checklist file to load, we look at the
            # properties and decide if we have to ask the user for additional
            # information about the checklist.
            #
            # Question for self:  Does it make sense to have the user verify all
            # the properties at load time or should the user only enter when the
            # properties are required and not loaded?
       
            
    #
    # Helper Functions
    # 

    def __load_checklist(self, checklist):
        filename = os.path.join('data', checklist)
        checkFile = gnomeglade.uninstalled_file(filename)
        if checkFile == None:
            filename = os.path.join(PROGRAMNAME, filename)
            checkFile = self.locate_file(gnome.FILE_DOMAIN_APP_DATADIR,
                    filename)
            if checkFile == []:
                checkFile = None
            else:
                checkFile = checkFile[0]
        if not checkFile:
            ### FIXME: We can select checklists via property, we need to
            # print error and recover.
            sys.stderr.write("Unable to find checklist: %s\n" % (filename))
            sys.exit(1)
        try:
            self.checklist = CheckList(checkFile)
        except (libxml2.parserError, libxml2.treeError, error.InvalidChecklist), msg:
            ### FIXME: We can select checklists via property, we need to
            # print error and recover.
            sys.stderr.write("Unable to parse the checklist: %s\n" % (msg))
            sys.exit(1)

        ### FIXME: We need to assemble the qamenu from the list of requested
        # checklist.functions instead of from the type variable.  Currently
        # breaking it totally by making it always pretend to have a SRPM.
        #
        # I think we'll have a module qamenu that takes a checklist as its
        # model.  The qamenu will instantiate a gtk.Menu suitable for calling
        # self.QAMenuItem.set_submenu() on.  The QAMenu will change when the
        # checklist model changes.
        #if self.checklist.type == 'SRPM':
        if True:
            from srpmqa import SRPMQA
            qamenu = SRPMQA(self)
        else:
            from genericqa import GenericQA
            qamenu = GenericQA(self)
        self.QAMenuItem.set_submenu(qamenu)
        qamenu.show_all()
        self.reviewView.set_model(self.checklist)
        ### FIXME: This must be replaced with a header method in the checklist.
        #self.reviewView.update_hash()
        self.reviewView.show()
        self.checkView.set_model(self.checklist)
        self.checkView.show()


    #
    # Menu/Toolbar callbacks
    #

    def on_menu_new_activate(self, *extra):
        '''Start a new review.'''
        checkload.NewDruid(self, checkload.NEW).show_all()

    def on_menu_open_activate(self, *extra):
        '''Open a saved review.'''
        checkload.NewDruid(self, checkload.LOAD).show_all()

    def on_menu_save_activate(self, *extra):
        """Save the current review to a file"""

        if self.checklist.filename:
            try:
                self.checklist.publish()
            except IOError, ex:
                errorDialog = gtk.MessageDialog(self.ReviewerWindow,
                        gtk.DIALOG_DESTROY_WITH_PARENT,
                        gtk.MESSAGE_WARNING,
                        gtk.BUTTONS_CLOSE,
                        'We were unable to save the review to the file you'
                        ' specified.  The error was:\n' + ex.msg +
                        '\n\nPlease select again.')
                errorDialog.set_title('Unable to save review')
                errorDialog.set_default_response(gtk.RESPONSE_CLOSE)
                response = errorDialog.run()
                errorDialog.destroy()
        else:
            self.on_menu_save_as_activate(extra)
        
    def on_menu_save_as_activate(self, *extra):
        """Save the current review to a file"""
       
        fileSelect = gtk.FileSelection(title='Select the file to save the review into.')
        if (os.path.isdir(self.lastSaveFileDir) and
                os.access(self.lastSaveFileDir, os.R_OK|os.X_OK)):
            fileSelect.set_filename(self.lastSaveFileDir)

        filename = None
        response = fileSelect.run()
        try:
            if response == gtk.RESPONSE_OK:
                filename = fileSelect.get_filename()
        finally:
            fileSelect.destroy()
            del fileSelect

        if filename:
            ### FIXME: Check if file exists
            # If so, prompt to overwrite
            self.lastSaveFileDir = os.path.dirname(filename)+'/'
            try:
                self.checklist.publish(filename)
            except IOError, ex:
                errorDialog = gtk.MessageDialog(self.ReviewerWindow,
                        gtk.DIALOG_DESTROY_WITH_PARENT,
                        gtk.MESSAGE_WARNING,
                        gtk.BUTTONS_CLOSE,
                        'We were unable to save the review to the file you'
                        ' specified.  The error was:\n' + ex.msg +
                        '\n\nPlease select again.')
                errorDialog.set_title('Unable to save review')
                errorDialog.set_default_response(gtk.RESPONSE_CLOSE)
                response = errorDialog.run()
                errorDialog.destroy()
                
    def on_menu_quit_activate(self, *extra):
        """End the program.

        Callback to end the program.
        """

        ### FIXME: Check for unsaved files.
        self.quit()
       
    def on_menu_cut_activate(self, *extra):
        '''Cut some text'''
        owner = self.clipPrimary.get_owner()
        if owner:
            if isinstance(owner, gtk.Editable):
                owner.cut_clipboard()
            else:
                ### FIXME: Is this behaviour consistent?
                # Or are apps supposed to fail if editing of the selection is
                # not allowed?
                selectionText = self.clipPrimary.wait_for_text()
                if selectionText:
                    self.clipboard.set_text(selectionText, -1)

    def on_menu_copy_activate(self, *extra):
        '''Copy from the current selection into the clipboard.'''
        if self.clipPrimary.get_owner():
            selectionText = self.clipPrimary.wait_for_text()
            if selectionText:
                self.clipboard.set_text(selectionText, -1)

    def on_menu_paste_activate(self, *extra):
        '''Copy from the clipboard into the selection.'''
        entry = self.ReviewerWindow.focus_widget
        if isinstance(entry, gtk.Editable):
            entry.paste_clipboard()

    def on_menu_preferences_activate(self, *extra):
        """Sets program properties."""
        gladeFile = gnomeglade.uninstalled_file('glade/qa-assistant.glade')
        if gladeFile == None:
            filename = os.path.join(PROGRAMNAME, 'glade/qa-assistant.glade')
            gladeFile = self.locate_file(gnome.FILE_DOMAIN_APP_DATADIR,
                    filename)
            if gladeFile == []:
                raise Exception("Unable to locate glade file %s" % (filename))
            else:
                gladeFile = gladeFile[0]

        prefDialog = Preferences(gladeFile)
        if self.logo:
            prefDialog.PreferencesDialog.set_icon(self.logo)

        prefDialog.PreferencesDialog.show()

    def on_menu_view_toggle_preview_activate(self, *extra):
        """Toggles between checklist view and output view.

        Keyword -- arguments:
        extra: user data.  Unused.

        We have two view modes at the moment.  One displays the output
        in line with the checklist items.  The other displays the items
        as they will appear in the QA Review.  This callback toggles between
        the two sets.
        """

        if self.grabArrow.get_property('arrow-type') == gtk.ARROW_LEFT:
            self.grabArrow.set(gtk.ARROW_RIGHT, gtk.SHADOW_NONE)
            self.checkView.display_output(False)
            self.reviewScroll.show()
        else:
            self.grabArrow.set(gtk.ARROW_LEFT, gtk.SHADOW_NONE)
            self.checkView.display_output(True)
            self.reviewScroll.hide()
            
    def on_menu_about_activate(self, *extra):
        """Show the about window."""

        gladeFile = gnomeglade.uninstalled_file('glade/qa-assistant.glade')
        if gladeFile == None:
            filename = os.path.join(PROGRAMNAME, 'glade/qa-assistant.glade')
            gladeFile = self.locate_file(gnome.FILE_DOMAIN_APP_DATADIR,
                    filename)
            if gladeFile == []:
                raise Exception("Unable to locate glade file %s" % (filename))
            else:
                gladeFile = gladeFile[0]

        about = gtk.glade.XML(gladeFile, 'AboutWindow').get_widget('AboutWindow')
        about.set_property('name', HUMANPROGRAMNAME)
        about.set_property('version', __version__)
        if self.logo:
            about.set_property('icon', self.logo)
            about.set_property('logo', self.logo)

        about.show()
        del(about)
       
    def on_toolbar_new_activate(self, button, *extra):
        """Popup the menu to select a new review from bugzilla or SRPM"""
        self.on_menu_new_activate()
       
    ### FIXME: This is totally broken
    def on_menu_new_srpm_activate(self, *extra):
        """Open a new review based on the user selected SRPM"""

        fileSelect = gtk.FileSelection(title='Select an SRPM to load')
        if (os.path.isdir(self.lastSRPMDir) and
                os.access(self.lastSRPMDir, os.R_OK|os.X_OK)):
            fileSelect.set_filename(self.lastSRPMDir)

        fileSelect.hide_fileop_buttons()
        filename = None
        response = fileSelect.run()
        try:
            if response == gtk.RESPONSE_OK:
                filename = fileSelect.get_filename()
        finally:
            fileSelect.destroy()
            del fileSelect

        if filename:
            self.lastSRPMDir = os.path.dirname(filename)+'/'

            # load the checklist data (Associates itself with checkView)
            self.SRPM_into_properties(filename)
            self.__load_checklist('fedoraus.xml')
            self.checkView.set_model(self.checklist)

    ### FIXME: Features we want to implement but haven't had the time yet:
    def on_menu_submit_activate(self, *extra):
        """Submit a review to bugzilla."""
        msg = """Submits a review via Bugzilla XML-RPC.  Coolness factor, but Publish is a more important feature as it gives the user a greater ability to look review and modify the generated review.  When we get better editing features into the checklist this will be more important.
        
Relative Priority: Publish will be the primary submission for now.  This is an enhancement and should depend on having better editing of the review first."""
        self.not_yet_implemented(msg)
        pass

    def on_menu_new_bugzilla_activate(self, *extra):
        """Open a new review with bugzilla report ID"""
        msg = """Associates this review with a bugzilla report.  The program needs to be able to use this to pick out information from a bugzilla report in order to autodownload packages and otherwise set up an environment for reviewing.  Although definitely cool, there's a good deal of work necessary for this to work.
        
Relative priority: Enhancement sometime after new review from SRPM. (Rather low)"""
        self.not_yet_implemented(msg)
        pass

    def on_menu_properties_activate(self, *extra):
        """Set properties on the review."""
        msg = """Difference between preference and properties?  Preferences can be program preferences and properties can be review properties.  Good for things like bugzilla report number and such like.

Okay. So maybe it will hold all things that are created on a review once and then largely forgotten about (but someone might want to edit them later.)
        
Relative priority: Comes after New from SRPM but before feature enhancements like new_from_bugzilla & Submit to bugzilla."""
        self.not_yet_implemented(msg)
        pass

    def on_menu_help_activate(self, *extra):
        """Display program help."""
        msg = """There's currently no help file written so this is pretty useless.  When we write some documentation this will display the standard gnome help browser.
        
Relative Priority: Low.  There's too much programming to do for me to spend too much time documenting it right now.  However, as features of the code near staility, I'll start adding documentation."""
        self.not_yet_implemented(msg)
        pass
        
    # 
    # Other GUI callbacks
    # 
    def on_grabBar_clicked(self, *extra):
        return self.on_menu_view_toggle_preview_activate(self, *extra)

    def not_yet_implemented(self, msg = ""):

        gladeFile = gnomeglade.uninstalled_file('glade/qa-assistant.glade')
        if gladeFile == None:
            filename = os.path.join(PROGRAMNAME, 'glade/qa-assistant.glade')
            gladeFile = self.locate_file(gnome.FILE_DOMAIN_APP_DATADIR,
                    filename)
            if gladeFile == []:
                raise Exception("Unable to locate glade file %s" % (filename))
            else:
                gladeFile = gladeFile[0]

        NYI = gtk.glade.XML(gladeFile, 'NYIDialog')
        NYIDialog = NYI.get_widget('NYIDialog')
        NYIDialog.set_default_response(gtk.RESPONSE_CLOSE)
        NYIDialog.connect('response', lambda dialog, response: dialog.destroy())
        if msg:
            NYIMsg = NYI.get_widget('NYIMsg')
            tb = NYIMsg.get_buffer()
            tb.set_text(msg)
        NYIDialog.show()
        del(NYI)

    #
    # Other event callbacks
    #
    def on_delete_event(self, *extra):
        """Delete a window."""
        return self.on_menu_quit_activate()
