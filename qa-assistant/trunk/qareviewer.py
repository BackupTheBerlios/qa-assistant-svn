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
__programName__ = "qa-assistant"
__programHumanName__ = "QA Assistant"
__version__ = "0.3"
__revision__ = "$Rev$"

import libxml2
import gtk, gnome
import sys, os

import checklist
import gnomeglade
from properties import Properties
from optionrenderer import OptionCellRenderer
from review import Review
from treetips import TreeTips

class QAReviewer(gnomeglade.GnomeApp):
    #
    # Program Initialization
    # 
    def __init__(self, arguments):
        """Creates a new QA reviewer window.
           
        Keyword -- arguments:
        arguments: A commandline to process when setting up the environment
        """

        # Create the properties for this checklist
        ### FIXME: Properties is hard-coded right now.  Needs some love.
        self.properties = Properties('fedoraus.xml')

        # Load the interface
        gladefile = 'glade/qa-assistant.glade'
        gnomeglade.GnomeApp.__init__(self, __programName__, __version__,
                gladefile, 'ReviewerWindow')
        self.program.set_property(gnome.PARAM_HUMAN_READABLE_NAME, __programHumanName__)
        
        #
        # Create additional interface components
        #

        iconFile = self._GnomeApp__uninstalled_file('pixmaps/qa-icon.png')
        if iconFile == None:
            iconFile = self.locate_file(gnome.FILE_DOMAIN_APP_PIXMAP,
                                        'qa-icon.png')
            if iconFile == []:
                iconFile = None
            else:
                iconFile = iconFile[0]
        if iconFile:
            self.ReviewerWindow.set_property('icon', gnomeglade.load_pixbuf(iconFile))

        # Create a treeview for our listPane
        self.checkView = gtk.TreeView()
        self.checkView.set_rules_hint(True)
        
        # load the checklist data (Associates itself with checkView)
        self.__load_checklist()

        renderer = gtk.CellRendererToggle()
        renderer.set_radio(False)
        column = gtk.TreeViewColumn('Display', renderer,
                                    active=checklist.DISPLAY,
                                    visible=checklist.ISITEM)
        renderer.connect('toggled', self.display_toggle)
        self.checkView.append_column(column)

        renderer = OptionCellRenderer()
        column = gtk.TreeViewColumn('pass/fail', renderer,
                                    optionlist=checklist.RESLIST,
                                    selectedoption=checklist.RESOLUTION,
                                    mode=checklist.ISITEM)
        column.set_cell_data_func(renderer, self.__translate_option_mode)
        renderer.connect('changed', self.resolution_changed)
        self.checkView.append_column(column)
       
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Description', renderer,
                                    text=checklist.SUMMARY)
        self.checkView.append_column(column)
        
        renderer = gtk.CellRendererText()
        renderer.connect('edited', self.output_edited, self.checklist.tree)
        column = gtk.TreeViewColumn('Output', renderer,
                                    markup=checklist.OUTPUT,
                                    visible=checklist.DISPLAY,
                                    editable=checklist.DISPLAY)
        self.outputColumn = column
        self.checkView.append_column(column)

        self.tips = TreeTips(self.checkView, checklist.DESC)

        self.listPane.add(self.checkView)
        self.checkView.show()

        self.grabArrow=gtk.Arrow(gtk.ARROW_LEFT, gtk.SHADOW_NONE)
        self.grabArrow.set_size_request(4,4)
        label=self.grabBar.get_child()
        self.grabBar.remove(label)
        self.grabBar.add(self.grabArrow)
        self.grabArrow.show()

        self.reviewView = Review(self.checklist.tree, self.properties)
        self.reviewView.show()
        self.reviewPane.add(self.reviewView)
        self.reviewScroll.hide()

        #
        # Command line initialization
        #
        ### FIXME: take care of the command line args

        ### FIXME: Absolute dependence on arguments[1] being an SRPM without a
        # check to make sure of it.  Need to fix that up with cmd-line args.
        if len(arguments) == 2:
            self.__SRPM_into_properties(arguments[1])

        #
        # Blast off!
        #
        self.__check_readiness()
        self.ReviewerWindow.show()

    #
    # Helper Functions
    # 

    def __load_checklist(self):
        ### FIXME: When calling this function to load a new checklist, we
        # need to be careful.  There was a bug where loading a new checklist
        # was causing editing of cells to no longer work.  I think we have
        # to reload our checklistPane everytime we load a new checklist....
        # -- Some restructuring of code to do there.
        # -- May only need to make sure self.checklist.tree is set correctly?
        filename = os.path.join('data', self.properties.checklistName)
        checkFile = self._GnomeApp__uninstalled_file(filename)
        if checkFile == None:
            filename = os.path.join(__programName__, filename)
            checkFile = self.locate_file(gnome.FILE_DOMAIN_APP_DATADIR,
                    filename)
            if checkFile == []:
                checkFile = None
            else:
                checkFile = checkFile[0]
        if checkFile == None:
            ### FIXME: When we can select checklists via property, we need to
            # print error and recover.
            sys.stderr.write("Unable to find checklist: %s\n" % (filename))
            sys.exit(1)
        try:
            self.checklist = checklist.CheckList(checkFile, self.properties)
        except (libxml2.parserError, libxml2.treeError, checklist.Error), msg:
            ### FIXME: When we can select checklists via property, we need to
            # print error and recover.
            sys.stderr.write("Unable to parse the checklist: %s\n" % (msg))
            sys.exit(1)

        self.checkView.set_model(self.checklist.tree)

    def __SRPM_into_properties(self, filename):
        msg = "Please select 'New => From SRPM'\nor 'New => From Bugzilla' to start the QA process."
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
        self.reviewView.update_hash()


    def __check_readiness(self):
        """Checks whether an SRPM is loaded or not.

        This should be called everytime property.SRPM changes.
        """
        
        if self.properties.SRPM:
            SRPMName = os.path.basename(self.properties.SRPM.filename)
            self.mainWinAppBar.pop()
            self.mainWinAppBar.push(SRPMName)
            self.ReviewerWindow.set_title(__programHumanName__ + ' - ' +
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
            self.ReviewerWindow.set_title(__programHumanName__)
            self.mainWinAppBar.pop()
            self.mainWinAppBar.push("No SRPM selected")

    def __translate_option_mode(self, column, cell, model, iter):
        """Translate from header/item value to mode type.

        Keyword -- arguments:
        column: column we're rendering
        cell: cell to perform our transformation on
        model: tree model our data lives in
        iter: reference to the cell we're operating on

        The mode of the cell depends on whether it is a header/category or an
        item/entry.  However, that is a boolean value and the mode needs to
        be of mode type.  So this function selects the proper mode type
        depending on whether we're rendering a header or an entry.
        """
        item = cell.get_property('mode')
        if item:
            mode=gtk.CELL_RENDERER_MODE_ACTIVATABLE
        else:
            mode=gtk.CELL_RENDERER_MODE_INERT
        cell.set_property('mode', mode)

    #
    # Treeview Callbacks
    # 
    def output_edited(self, cell, row, newValue, model):
        """Change the text of the output string"""
        iter = model.get_iter_from_string(row)
        path = self.checklist.tree.get_path(iter)
        name = self.checklist.tree.get_value(iter, checklist.RESOLUTION)
        if name == 'Fail':
            color = self.properties.failColor
        elif name == 'Non-Blocker' or name == 'Needs-Reviewing':
            color = self.properties.minorColor
        elif name == 'Pass':
            color = self.properties.passColor
        else:
            color = None
        if color:
            newValue='<span foreground="' + color + '">' + newValue + '</span>'

        outDict = self.checklist.tree.get_value(iter, checklist.OUTPUTLIST)
        outDict[name] = newValue
        self.checklist.tree.set(iter, checklist.OUTPUT, newValue)
        self.checklist.tree.row_changed(path, iter)

    def resolution_changed(self, renderer, newValue, iter):
        """Changes the display when the user changes an item's state.

        Keyword -- arguments:
        renderer: renderer object emitting the signal
        newValue: resolution type we're changing to
        iter: iter pointing to the node in the tree we're operating on

        When the user changes the resolution of a checklist item, we need to
        change the value in our model.  Other parts of the model may also be
        affected by this change as well.
        """
        self.checklist.tree.set(iter, checklist.RESOLUTION, newValue)
        outputlist = self.checklist.tree.get_value(iter, checklist.OUTPUTLIST)
        out = outputlist[newValue]
        self.checklist.tree.set(iter, checklist.OUTPUT, out)
        path = self.checklist.tree.get_path(iter)
        self.checklist.tree.row_changed(path, iter)
        category = self.checklist.tree.iter_parent(iter)
        catRes = self.checklist.tree.get_value(category, checklist.RESOLUTION)

        ### FIXME: Should this go in its own function somewhere else?
        if newValue == 'Fail' or newValue == 'Non-Blocker':
            ### FIXME: Check preferences for auto-display on fail
            # Auto display to review if it's a fail
            self.checklist.tree.set(iter, checklist.DISPLAY, True)

        # Check if the change makes the overall review into a pass or fail
        if newValue == 'Fail':

            if catRes == 'Fail':
                return
        elif newValue == 'Needs-Reviewing':
            if catRes == 'Needs-Reviewing':
                return
            if catRes != 'Pass':
                iter = self.checklist.tree.iter_children(category)
                while iter:
                    nodeRes = self.checklist.tree.get_value(iter, checklist.RESOLUTION)
                    if nodeRes == 'Fail':
                        return
                    iter = self.checklist.tree.iter_next(iter)
        elif (newValue == 'Pass' or newValue == 'Not-Applicable' or 
                newValue == 'Non-Blocker'):
            newValue = 'Pass'
            iter = self.checklist.tree.iter_children(category)
            while iter:
                nodeRes = self.checklist.tree.get_value(iter, checklist.RESOLUTION)
                if nodeRes == 'Needs-Reviewing':
                    newValue = 'Needs-Reviewing'
                elif nodeRes == 'Fail':
                    return
                iter = self.checklist.tree.iter_next(iter)

        self.checklist.tree.set(category, checklist.RESOLUTION, newValue)
        path = self.checklist.tree.get_path(category)
        self.checklist.tree.row_changed(path, category)

    def display_toggle(self, cell, path, *data):
        """Toggles outputting a message for the review.

        Keyword -- arguments:
        cell: displayed cell we were called on
        path: path to the cell
        data: additional user data.  None for now.

        The display toggle allows the user to choose whether to write a
        message about the Pass or Failure state of the reviewed item.  This
        callback takes care of setting the state in the TreeStore.
        """ 
        
        iter = self.checklist.tree.get_iter(path)
        value = self.checklist.tree.get_value(iter, checklist.DISPLAY)
        name = self.checklist.tree.get_value(iter, checklist.SUMMARY)

        if value == True:
            self.checklist.tree.set(iter, checklist.DISPLAY, False) 
            pass
        else:
            self.checklist.tree.set(iter, checklist.DISPLAY, True)

    #
    # Menu/Toolbar callbacks
    #
    
    def on_menu_publish_activate(self, *extra):
        """Publish a review to a file."""
        
        # Check that the review is in a completed state
        if self.reviewView.resolution.get_text() == 'Incomplete Review':
            msgDialog = gtk.MessageDialog(self.ReviewerWindow,
                    gtk.DIALOG_DESTROY_WITH_PARENT,
                    gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                    'You have not checked all items in the checklist so the review is incomplete.  Are you sure you want to submit a review based on the current work?')
            msgDialog.set_title('Incomplete review: submit anyway?')
            response = msgDialog.run()
            msgDialog.destroy()
            if response == gtk.RESPONSE_NO:
                return
        
        # File select dialog for use in file selecting callbacks.
        fileSelect = gtk.FileSelection(title='Select a file to publish the review into')
        if (os.path.isdir(self.properties.lastSRPMDir) and
                os.access(self.properties.lastSRPMDir, os.R_OK|os.X_OK)):
            fileSelect.set_filename(self.properties.lastReviewDir)
        response = fileSelect.run()
        try:
            if response == gtk.RESPONSE_OK:
                filename = fileSelect.get_filename()
                self.properties.lastReviewDir = os.path.dirname(filename)+'/'
                self.reviewView.publish(fileSelect.get_filename())
        finally:
            fileSelect.destroy()
            del fileSelect

    def on_menu_quit_activate(self, *extra):
        """End the program.

        Callback to end the program.
        """

        ### FIXME: Check for unsaved files.
        self.quit()
       
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
            self.checkView.remove_column(self.outputColumn)
            self.reviewScroll.show()
        else:
            self.grabArrow.set(gtk.ARROW_LEFT, gtk.SHADOW_NONE)
            self.checkView.append_column(self.outputColumn)
            self.reviewScroll.hide()
            
    def on_menu_about_activate(self, *extra):
        """Show the about window."""

        gladeFile = self._GnomeApp__uninstalled_file('glade/qa-assistant.glade')
        if gladeFile == None:
            filename = os.path.join(__programName__, 'glade/qa-assistant.glade')
            gladeFile = self.locate_file(gnome.FILE_DOMAIN_APP_DATADIR,
                    filename)
            if gladeFile == []:
                raise Exception("Unable to locate glade file %s" % (filename))
            else:
                gladeFile = gladeFile[0]

        about = gtk.glade.XML(gladeFile, 'AboutWindow').get_widget('AboutWindow')
        about.set_property('name', __programHumanName__)
        about.set_property('version', __version__)
        iconFile = self._GnomeApp__uninstalled_file('pixmaps/qa-icon.png')
        if iconFile == None:
            iconFile = self.locate_file(gnome.FILE_DOMAIN_APP_PIXMAP,
                                        'qa-icon.png')
            if iconFile == []:
                iconFile = None
            else:
                iconFile = iconFile[0]
        if iconFile:
            icon = gnomeglade.load_pixbuf(iconFile)
            about.set_property('icon', icon)
            about.set_property('logo', icon)

        about.show()
       
    def on_toolbar_new_activate(self, button, *extra):
        """Popup the menu to select a new review from bugzilla or SRPM"""

        ### FIXME: pygtk bug
        # In pygtk 2.0 get_current_event_time returns a Python Long but
        # menu.popup expects a Python Int.  The problem arises because the
        # time is a guint32 which causes problems because Python does not have
        # an unsigned int type
        # This hack munges current_event_time to match what event.time
        # provides but it's less than ideal.
        time = gtk.get_current_event_time()
        offset = time - int(0x7FFFFFFF)
        if offset > 0:
            time = int(-2147483648 + offset)

        self.new1_menu.popup(None, None, None, 0, time)
        
    def on_menu_new_srpm_activate(self, *extra):
        """Open a new review based on the user selected SRPM"""

        fileSelect = gtk.FileSelection(title='Select an SRPM to load')
        if (os.path.isdir(self.properties.lastSRPMDir) and
                os.access(self.properties.lastSRPMDir, os.R_OK|os.X_OK)):
            fileSelect.set_filename(self.properties.lastSRPMDir)

        fileSelect.hide_fileop_buttons()
        response = fileSelect.run()
        try:
            if response == gtk.RESPONSE_OK:
                filename = fileSelect.get_filename()
                self.properties.lastSRPMDir = os.path.dirname(filename)+'/'
                self.__SRPM_into_properties(filename)
        finally:
            fileSelect.destroy()
            del fileSelect

    ### FIXME: Features we want to implement but haven't had the time yet:
    def on_menu_submit_activate(self, *extra):
        """Submit a review to bugzilla."""
        msg = """Submits a review via Bugzilla XML-RPC.  Coolness factor, but Publish is a more important feature as it gives the user a greater ability to look review and modify the generated review.  When we get better editing features into the checklist this will be more important.
        
Relative Priority: Publish will be the primary submission for now.  This is an enhancement and should depend on having better editing of the review first."""
        self.not_yet_implemented(msg)
        pass

    def on_menu_open_activate(self, *extra):
        """Open a saved review"""
        msg = """Open a saved review. In the future, this function will allow us to access a review that we've already saved.

Relative priority: after save functionality."""
        self.not_yet_implemented(msg)
        pass

    def on_menu_save_activate(self, *extra):
        """Save the current review to a file"""
        msg = """Saves a review to a file.  This is a snapshot of the review at this moment.  The publish/submit features will allow one to print the review out and submit to bugzilla.
        
Relative priority: Publish is more important."""
        self.not_yet_implemented(msg)
        pass

    def on_menu_save_as_activate(self, *extra):
        """Save the current review to a file"""
        msg = """Saves a review to a file.  This is a snapshot of the review at this moment.  The publish/submit features will allow one to print the review out and submit to bugzilla.
        
Relative priority: Publish is more important."""
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

    def on_menu_preferences_activate(self, *extra):
        """Sets program properties."""
        msg = """Please see the PREFERENCES file for a list of preferences that are going to be added to oreferences once we get GConf set up.

Relative Priority: Not before the first release.  Sensible defaults is my hope for that release."""
        self.not_yet_implemented(msg)
        pass

    def on_menu_help_activate(self, *extra):
        """Display program help."""
        msg = """There's currently no help file written so this is pretty useless.  When we write some documentation this will display the standard gnome help browser.
        
Relative Priority: _Low_.  Developers are going to use this, not end-users so a willingness to use something that's relatively undocumented is expected."""
        self.not_yet_implemented(msg)
        pass
        
    ### FIXME: Part 2: Editing features are not currently encouraged.
    # Have to recconcile these with our need to keep each checklist item in
    # its place.
    def on_menu_cut_activate(self, *extra):
        """Cut some text"""
        self.not_yet_implemented()
        pass

    def on_menu_copy_activate(self, *extra):
        """Copy some text"""
        self.not_yet_implemented()
        pass

    def on_menu_paste_activate(self, *extra):
        """Paste some text"""
        self.not_yet_implemented()
        pass

    def on_menu_clear_activate(self, *extra):
        """Clear some text"""
        self.not_yet_implemented()
        pass

    # 
    # Other GUI callbacks
    # 
    def on_grabBar_clicked(self, *extra):
        return self.on_menu_view_toggle_preview_activate(self, *extra)

    def not_yet_implemented(self, msg = ""):
        NYI = gtk.glade.XML('glade/qa-assistant.glade', 'NYIDialog')
        NYIDialog = NYI.get_widget('NYIDialog')
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
