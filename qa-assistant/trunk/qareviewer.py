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
__version__ = "0.4"
__revision__ = "$Rev$"

import sys
import os
import libxml2
import gtk
import gnome

import checklist
import gnomeglade
import error
from properties import Properties
from optionrenderer import OptionCellRenderer
from review import Review
from treetips import TreeTips
from savefile import SaveFile

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
        
        ### FIXME: Merge with checklist.

        # Create a structure providing savefiles
        self.saveFile = SaveFile(self, None)

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
        column = gtk.TreeViewColumn('Resolution', renderer,
                                    optionlist=checklist.RESLIST,
                                    selectedoption=checklist.RESOLUTION,
                                    mode=checklist.ISITEM)
        column.set_cell_data_func(renderer, self.__translate_option_mode)
        renderer.connect('changed', self.resolution_changed)
        self.checkView.append_column(column)
       
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Summary', renderer,
                                    text=checklist.SUMMARY)
        self.checkView.append_column(column)
        
        renderer = gtk.CellRendererText()
        renderer.connect('edited', self.output_edited)
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

        self.reviewScroll.hide()

        #
        # Command line initialization
        #
        ### FIXME: take care of the command line args

        ### FIXME: Absolute dependence on arguments[1] being an SRPM without a
        # check to make sure of it.  Need to fix that up with cmd-line args.
        if len(arguments) == 2:
            self.SRPM_into_properties(arguments[1])

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
        # -- May only need to make sure self.checklist is set correctly?
        filename = os.path.join('data', self.properties.checklist)
        checkFile = gnomeglade.uninstalled_file(filename)
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
            self.checklist = checklist.CheckList(checkFile)
        except (libxml2.parserError, libxml2.treeError, error.InvalidChecklist), msg:
            ### FIXME: When we can select checklists via property, we need to
            # print error and recover.
            sys.stderr.write("Unable to parse the checklist: %s\n" % (msg))
            sys.exit(1)

        self.checkView.set_model(self.checklist)

        ### FIXME: We need to assemble the qamenu from the list of requested
        # checklist.functions instead of from the type variable.  Currently
        # breaking it totally by making it always pretend to have a SRPM.
        #if self.checklist.type == 'SRPM':
        if True:
            from srpmqa import SRPMQA
            qamenu = SRPMQA(self)
        else:
            from genericqa import GenericQA
            qamenu = GenericQA(self)
        self.QAMenuItem.set_submenu(qamenu)
        qamenu.show_all()
        try:
            self.reviewView.destroy()
        except AttributeError:
            # No problems as long as reviewView doesn't exist
            pass
        self.reviewView = Review(self.checklist, self.properties)
        self.reviewView.update_hash()
        self.reviewView.show()
        self.reviewPane.add(self.reviewView)
        self.saveFile.set_checklist(self.checklist)

    def SRPM_into_properties(self, filename):
        '''Add an SRPM file into our properties structure.
        
        Keyword -- arguments:
        filename -- filename of the SRPM

        Sets our properties to use the specified SRPM file for the checklist.
        '''
        
        msg = 'Please select "QA Action => From SRPM"\nor "QA Action => From Bugzilla" to start the QA process.'
        self.properties.lastSRPMDir = os.path.dirname(filename)+'/'
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

    def __translate_option_mode(self, column, cell, model, rowIter):
        """Translate from header/item value to mode type.

        Keyword -- arguments:
        column: column we're rendering
        cell: cell to perform our transformation on
        model: tree model our data lives in
        rowIter: reference to the cell we're operating on

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
    def output_edited(self, cell, row, newValue):
        """Change the text of the output string"""
        rowIter = self.checklist.get_iter_from_string(row)
        path = self.checklist.get_path(rowIter)
        name = self.checklist.get_value(rowIter, checklist.RESOLUTION)
        newValue = self.checklist.pangoize_output(name, newValue)

        outDict = self.checklist.get_value(rowIter, checklist.OUTPUTLIST)
        outDict[name] = newValue
        self.checklist.set(rowIter, checklist.OUTPUT, newValue)
        self.checklist.row_changed(path, rowIter)

    ### FIXME: I believe this should go into checklist.  Possibly this whole
    # section belongs in checklist.
    def resolution_changed(self, renderer, newValue, changedRow):
        """Changes the display when the user changes an item's state.

        Keyword -- arguments:
        renderer: renderer object emitting the signal
        newValue: resolution type we're changing to
        changedRow: iter pointing to the node in the tree we're operating on

        When the user changes the resolution of a checklist item, we need to
        change the value in our model.  Other parts of the model may also be
        affected by this change as well.
        """

        # Set the checklist to the new resolution and output values
        self.checklist.set(changedRow, checklist.RESOLUTION, newValue)
        outputlist = self.checklist.get_value(changedRow, checklist.OUTPUTLIST)
        out = outputlist[newValue]
        self.checklist.set(changedRow, checklist.OUTPUT, out)
        
        # Signal that this row has been changed
        path = self.checklist.get_path(changedRow)
        self.checklist.row_changed(path, changedRow)

        # Load category information to check if it needs updating too.
        category = self.checklist.iter_parent(changedRow)
        catRes = self.checklist.get_value(category, checklist.RESOLUTION)

        if newValue == 'Fail' or newValue == 'Non-Blocker':
            ### FIXME: Check preferences for auto-display on fail
            # Auto display to review if it's a fail
            self.checklist.set(changedRow, checklist.DISPLAY, True)

        # Check if the change makes the overall review into a pass or fail
        if newValue == 'Fail':
            # Unless it's already set to Fail, we'll change it.
            if catRes == 'Fail':
                return
        elif newValue == 'Needs-Reviewing':
            # If there's no entries for Fail, we'll change to Needs-Reviewing
            if catRes == 'Needs-Reviewing':
                return
            if catRes != 'Pass':
                entryIter = self.checklist.iter_children(category)
                while changedRow:
                    nodeRes = self.checklist.get_value(entryIter,
                            checklist.RESOLUTION)
                    if nodeRes == 'Fail':
                        return
                    changedRow = self.checklist.iter_next(entryIter)
        elif (newValue == 'Pass' or newValue == 'Not-Applicable' or 
                newValue == 'Non-Blocker'):
            # Unless another entry is Fail or Needs-Reviewing, change to Pass
            newValue = 'Pass'
            entryIter = self.checklist.iter_children(category)
            while entryIter:
                nodeRes = self.checklist.get_value(entryIter, checklist.RESOLUTION)
                if nodeRes == 'Needs-Reviewing':
                    newValue = 'Needs-Reviewing'
                elif nodeRes == 'Fail':
                    return
                entryIter = self.checklist.iter_next(entryIter)

        self.checklist.set(category, checklist.RESOLUTION, newValue)
        path = self.checklist.get_path(category)
        self.checklist.row_changed(path, category)

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
        
        entryIter = self.checklist.get_iter(path)
        value = self.checklist.get_value(rowIter, checklist.DISPLAY)

        if value:
            self.checklist.set(entryIter, checklist.DISPLAY, False)
        else:
            self.checklist.set(entryIter, checklist.DISPLAY, True)

    #
    # Menu/Toolbar callbacks
    #

    def on_menu_open_activate(self, *extra):
        """Open a saved review"""
        fileSelect = gtk.FileSelection(title='Select the checklist file to load.')
        if (os.path.isdir(self.properties.lastSaveFileDir) and
                os.access(self.properties.lastSaveFileDir, os.R_OK|os.X_OK)):
            fileSelect.set_filename(self.properties.lastSaveFileDir)

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
            self.properties.lastSaveFileDir = os.path.dirname(filename)+'/'
            self.saveFile.set_filename(filename)
            try:
                newList = self.saveFile.load()
            except IOError, msg:
                ### FIXME: MSG Dialog that we were unable to load the file
                pass

            try:
                self.checklist.destroy()
            except AttributeError:
                # No problems as long as checklist no longer exists.
                pass
            self.checklist = newList
            ### FIXME: The following is copied from SRPM_into_properties
            # It needs to be refactored to just have one copy somewhere.
            self.__check_readiness()
            ### End of SRPM into properties
            
            ### FIXME: This is copied from __load_checklist().
            # __load_checklist needs to be split to have this method...
            # sync_checklist which will perform this sync of checklistView to
            # data.  And a load_checklist which is a special case of this
            # function (and thus should be merged with it.)
            self.checkView.set_model(self.checklist)
            
            if self.checklist.type == 'SRPM':
                from srpmqa import SRPMQA
                qamenu = SRPMQA(self)
            else:
                from genericqa import GenericQA
                qamenu = GenericQA(self)
            self.QAMenuItem.set_submenu(qamenu)
            qamenu.show_all()
            try:
                self.reviewView.destroy()
            except AttributeError:
                # No problems as long as reviewView no longer exists.
                pass
            self.reviewView = Review(self.checklist, self.properties)
            self.reviewView.update_hash()
            self.reviewView.show()
            self.reviewPane.add(self.reviewView)
            self.saveFile.set_checklist(self.checklist)
            ### End of __load_checklist copy.

    def on_menu_save_activate(self, *extra):
        """Save the current review to a file"""

        if self.saveFile.filename:
            try:
                self.saveFile.publish()
            except IOError, msg:
                ### FIXME: MSG Dialog that we were unable to save this file
                pass
        else:
            self.on_menu_save_as_activate(extra)
        
    def on_menu_save_as_activate(self, *extra):
        """Save the current review to a file"""
       
        fileSelect = gtk.FileSelection(title='Select the file to save the review into.')
        if (os.path.isdir(self.properties.lastSaveFileDir) and
                os.access(self.properties.lastSaveFileDir, os.R_OK|os.X_OK)):
            fileSelect.set_filename(self.properties.lastSaveFileDir)

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
            self.properties.lastSaveFileDir = os.path.dirname(filename)+'/'
            self.saveFile.set_filename(filename)
            try:
                self.saveFile.publish()
            except IOError, msg:
                ### FIXME: MSG Dialog that we were unable to save the file
                pass
                
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

        gladeFile = gnomeglade.uninstalled_file('glade/qa-assistant.glade')
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
        iconFile = gnomeglade.uninstalled_file('pixmaps/qa-icon.png')
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
        # -- This has been fixed in 2.2.0 have to require that?
        """
        time = gtk.get_current_event_time()
        offset = time - int(0x7FFFFFFF)
        if offset > 0:
            time = int(-2147483648 + offset)
        """
        self.new1_menu.popup(None, None, None, 0, gtk.get_current_event_time())
        
    def on_menu_new_srpm_activate(self, *extra):
        """Open a new review based on the user selected SRPM"""

        fileSelect = gtk.FileSelection(title='Select an SRPM to load')
        if (os.path.isdir(self.properties.lastSRPMDir) and
                os.access(self.properties.lastSRPMDir, os.R_OK|os.X_OK)):
            fileSelect.set_filename(self.properties.lastSRPMDir)

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
            self.properties.lastSRPMDir = os.path.dirname(filename)+'/'

            # load the checklist data (Associates itself with checkView)
            self.SRPM_into_properties(filename)
            self.__load_checklist()
            # Reset savefile so we don't accidentally overwrite something.
            self.saveFile.set_filename(None)

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

    def on_menu_preferences_activate(self, *extra):
        """Sets program properties."""
        msg = """Please see the PREFERENCES file for a list of preferences that are going to be added to preferences once we get GConf set up.

Relative Priority: Not before the first release.  Sensible defaults is my hope for that release."""
        self.not_yet_implemented(msg)
        pass

    def on_menu_help_activate(self, *extra):
        """Display program help."""
        msg = """There's currently no help file written so this is pretty useless.  When we write some documentation this will display the standard gnome help browser.
        
Relative Priority: Low.  There's too much programming to do for me to spend too much time documenting it right now.  However, as features of the code near staility, I'll start adding documentation."""
        self.not_yet_implemented(msg)
        pass
        
    ### FIXME: Part 2: Editing features are not currently encouraged.
    # Have to reconcile these with our need to keep each checklist item in
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

        gladeFile = gnomeglade.uninstalled_file('glade/qa-assistant.glade')
        if gladeFile == None:
            filename = os.path.join(__programName__, 'glade/qa-assistant.glade')
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
