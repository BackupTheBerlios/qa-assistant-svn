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

from qaglobals import *
import gnomeglade
import ui
import error
import checkload
from review import Review
import checklist
from checkview import CheckView
from preferences import Preferences
from propview import PropertiesDialog

__version__ = VERSION

class QAReviewer(gnomeglade.GnomeApp):
    '''Main Program Object.

    '''
    def __init__(self, arguments):
        """Creates a new QA reviewer window.
           
        Keyword -- arguments:
        arguments: A commandline to process when setting up the environment
        """

        # Load the main part of the interface
        gladefile = 'glade/qa-assistant.glade'
        gnomeglade.GnomeApp.__init__(self, PROGRAMNAME, __version__,
                HUMANPROGRAMNAME, gladefile, 'ReviewerWindow')
       
        #
        # Create additional interface components
        #

        # Create a uimanager to handle the menus and toolbars
        self.uiManager = ui.UI(self)
        self.mergedMenus = {}
        accelGroup = self.uiManager.get_accel_group()
        self.ReviewerWindow.add_accel_group(accelGroup)
        menubar = self.uiManager.get_widget('/MainMenu')
        toolbar = self.uiManager.get_widget('/MainToolBar')
        self.ReviewerWindow.set_menus(menubar)
        self.ReviewerWindow.set_toolbar(toolbar)
        iconFile = gnomeglade.uninstalled_file('pixmaps/qa-icon.png')
        if iconFile == None:
            iconFile = self.program.locate_file(gnome.FILE_DOMAIN_APP_PIXMAP,
                                        'qa-icon.png', True)
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

        self.grabArrow = gtk.Arrow(gtk.ARROW_LEFT, gtk.SHADOW_NONE)
        self.grabArrow.set_size_request(4,4)
        label = self.grabBar.get_child()
        self.grabBar.remove(label)
        self.grabBar.add(self.grabArrow)
        self.grabArrow.show()

        self.reviewScroll.hide()

        # Create our Clipboard
        self.clipboard = gtk.Clipboard(gtk.gdk.display_get_default(),
                'CLIPBOARD')
        self.clipPrimary = gtk.Clipboard(gtk.gdk.display_get_default(),
                'PRIMARY')

        self.lastSaveFileDir = './'
        ### FIXME: This should be set by the module that consumes it.
        #self.lastSRPMDir = './'

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
            checkFile = self.program.locate_file(gnome.FILE_DOMAIN_APP_DATADIR,
                    filename, True)
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
            self.checklist = checklist.CheckList(checkFile)
        except (libxml2.parserError, libxml2.treeError, error.InvalidChecklist), msg:
            ### FIXME: We can select checklists via property, we need to
            # print error and recover.
            sys.stderr.write("Unable to parse the checklist: %s\n" % (msg))
            sys.exit(1)

        # Reset the checklist specific ui elements
        for menu in self.mergedMenus.keys():
            self.uiManager.remove_ui(menu)
            self.uiManager.remove_action_group(self.mergedMenus[menu])
        self.mergedMenus = {}

        # Insert the new uiManager stuff
        qamenudata = self.checklist.functions.get_ui(self)
        for (actions, menus) in qamenudata:
            self.uiManager.insert_action_group(actions, 50)
            mergeId = self.uiManager.add_ui_from_string(menus)
            self.mergedMenus[mergeId] = actions
            
        self.reviewView.set_model(self.checklist)
        self.reviewView.show()
        self.checkView.set_model(self.checklist)
        self.checkView.show()

    #
    # Base Action Callbacks
    #
    def new_cb(self, action, extra):
        '''Start a new review.'''
        checkload.NewDruid(self, checkload.NEW).show_all()

    def open_cb(self, action, extra):
        '''Open a saved review.'''
        checkload.NewDruid(self, checkload.LOAD).show_all()

    def quit_cb(self, action, extra):
        '''End the program.

        Callback to end the program.
        '''
        ### FIXME: Check for unsaved files.
        gtk.main_quit()

    def preferences_cb(self, action, extra):
        '''Sets program properties.'''
        gladeFile = gnomeglade.uninstalled_file('glade/qa-assistant.glade')
        if gladeFile == None:
            filename = os.path.join(PROGRAMNAME, 'glade/qa-assistant.glade')
            gladeFile = self.program.locate_file(gnome.FILE_DOMAIN_APP_DATADIR,
                    filename, True)
            if gladeFile == []:
                ### FIXME: Less generic exception here.
                raise Exception("Unable to locate glade file %s" % (filename))
            else:
                gladeFile = gladeFile[0]

        prefDialog = Preferences(gladeFile)
        if self.logo:
            prefDialog.PreferencesDialog.set_icon(self.logo)

        prefDialog.PreferencesDialog.show()

    def help_cb(self, action, extra):
        '''Display program help.'''
        msg = """There's currently no help file written so this is pretty useless.  When we write some documentation this will display the standard gnome help browser.
        
Relative Priority: Low.  The program is currently changing too fast to document well.  However, as features of the code near staility, I'll start adding documentation."""
        self.not_yet_implemented(msg)
        # gnome.help_display('qa-assistant')
        pass

    def about_cb(self, action, extra):
        '''Show the about window.'''

        ### FIXME: Should either put this in a separate glade file or
        # implement it in code so we don't have to load the whole glade file.
        gladeFile = gnomeglade.uninstalled_file('glade/qa-assistant.glade')
        if gladeFile == None:
            filename = os.path.join(PROGRAMNAME, 'glade/qa-assistant.glade')
            gladeFile = self.program.locate_file(gnome.FILE_DOMAIN_APP_DATADIR,
                    filename, True)
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
    
    #
    # Checklist Action Callbacks
    #

    def cut_cb(self, action, extra):
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

    def copy_cb(self, action, extra):
        '''Copy from the current selection into the clipboard.'''
        if self.clipPrimary.get_owner():
            selectionText = self.clipPrimary.wait_for_text()
            if selectionText:
                self.clipboard.set_text(selectionText, -1)

    def paste_cb(self, action, extra):
        '''Copy from the clipboard into the selection.'''
        entry = self.ReviewerWindow.focus_widget
        if isinstance(entry, gtk.Editable):
            entry.paste_clipboard()

    def properties_cb(self, action, extra):
        '''Pops up a dialog that allows us to set the CheckList properties.'''
        propDialog = PropertiesDialog(self.checklist.properties)
        if self.logo:
            propDialog.set_icon(self.logo)

        propDialog.show()

    def toggle_preview_cb(self, action, extra):
        '''Toggles between checklist view and output view.

        Keyword -- arguments:
        action: The action that invoked the callback.
        extra: user data.  Unused.

        We have two view modes at the moment.  One displays the output
        in line with the checklist items.  The other displays the items
        as they will appear in the QA Review.  This callback toggles between
        the two sets.
        '''
        if self.grabArrow.get_property('arrow-type') == gtk.ARROW_LEFT:
            self.grabArrow.set(gtk.ARROW_RIGHT, gtk.SHADOW_NONE)
            self.checkView.display_output(False)
            self.reviewScroll.show()
        else:
            self.grabArrow.set(gtk.ARROW_LEFT, gtk.SHADOW_NONE)
            self.checkView.display_output(True)
            self.reviewScroll.hide()
    
    #
    # Modified action group
    #

    def save_cb(self, action, extra):
        '''Save the current review to a file.'''
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
            self.save_as_cb(action, extra)

    def save_as_cb(self, action, extra):
        '''Save the current review to a file.'''
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


    #
    # Menu/Toolbar callbacks
    #

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

        
    # 
    # Other GUI callbacks
    # 
    def on_grabBar_clicked(self, *extra):
        return self.toggle_preview_cb(self, None, *extra)

    def not_yet_implemented(self, msg = ""):

        gladeFile = gnomeglade.uninstalled_file('glade/qa-assistant.glade')
        if gladeFile == None:
            filename = os.path.join(PROGRAMNAME, 'glade/qa-assistant.glade')
            gladeFile = self.program.locate_file(gnome.FILE_DOMAIN_APP_DATADIR,
                    filename, True)
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
        return self.quit_cb(None, None)
