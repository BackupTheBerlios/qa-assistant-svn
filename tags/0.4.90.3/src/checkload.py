# File: checkload.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 26 October, 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
'''A QA Assistant druid for starting new checklists.
'''
__revision__ = '$Rev$'

import os
import libxml2

import gtk
import gobject
import gnome.ui

from qaconst import *
import error
from checklist import CheckList
from propview import PropertiesView

#
# Druid Modes
#
START = 1   # Druid to display on startup
NEW = 2     # Druid to help when creating a new review
LOAD = 3    # Druid to use when loading a review
PROPERTIES = 4 # Druid to use when changing properties

class NewDruid(gtk.Window):
    '''Druid to walk through starting a new review

    '''
    __FILENAME = 0
    __CHECKNAME = 1
    __CHECKSUMMARY = 2

    def __init__(self, app, mode=None):
        # Create the druid
        self.app = app
        self.logo = app.logo
        gtk.Window.__init__(self)
        self.druidWidget = gnome.ui.Druid()
        self.add(self.druidWidget)
        self.druidWidget.set_show_help(True)
        self.druidWidget.connect('cancel', self.close_druid)
        self.connect('destroy_event', self.close_druid)
        mode = mode or START
        self.mode = mode

        if mode == START:
            self.build_start_fresh()
        if mode == START or mode == NEW:
            # Figure out which items are in the site checklists directory
            checklistDirName = os.path.join(PROGRAMNAME, 'data')
            ### FIXME: Expand qaDataDir to include checklists in user
            # directories
            qaDataDir = app.locate_file(gnome.FILE_DOMAIN_APP_DATADIR,
                    checklistDirName)
            checklists = []
            for directory in qaDataDir:
                files = os.listdir(directory)
                for oneFile in files:
                    if oneFile.endswith('.xml'):
                        checklists.append(os.path.join(directory, oneFile))
            self.build_selector(checklists)
        if mode == START or mode == LOAD:
            # Create the sequence of pages for selecting a checklist to load
            self.build_loader()

        # Required Properties
        self.build_properties()

        # Create end page
        self.build_end()

        if mode == LOAD:
            self.set_title('QA Assistant - Load a Saved QA Review')
            # Disable going back from loaderPage b/c it's the first page
            self.druidWidget.set_buttons_sensitive(False, True, True, True)
            self.propertiesPage.connect('back', self.disable_back,
                    self.loaderPage)
        elif mode == NEW:
            self.set_title('QA Assistant - Start a new QA Review')
            # Disable going back from selectorPage b/c it's the first page
            self.druidWidget.set_buttons_sensitive(False, True, True, True)
            self.propertiesPage.connect('back', self.disable_back,
                    self.selectorPage)
        elif mode == PROPERTIES:
            self.set_title('QA Assistant - Set Properties')
            self.druidWidget.set_buttons_sensitive(False, True, True, True)
            self.druidWidget.set_finish()
        else:
            self.set_title('QA Assistant - Starting a QA Review')
            # Coming back from propertiesPage has to determine whether it came
            # from selectorPage or loadPage.
            self.propertiesPage.connect('back', self.properties_back)

    #
    # Page creation methods
    #
    
    def build_start_fresh(self):
        '''Builds pages to decide how the user wants to create the review.

        '''
        startPage = gnome.ui.DruidPageEdge(gnome.ui.EDGE_START)
        startPage.set_title('Start a new QA Review')
        startPage.set_logo(self.logo)
        startPage.set_text('Welcome to QA Assistant, a program for creating'
                ' Quality Assurance Reviews.  QA Assistant uses the concept'
                ' of filling out a checklist to generate a QA Report.  This'
                ' Druid will walk you through the process of starting a new'
                ' QA Review using QA Assistant checklists.')
        self.druidWidget.add(startPage)

        # Create first entry page with New review vs Open existing checkbox.
        choicePage = gnome.ui.DruidPageStandard()
        self.choicePage = choicePage
        choicePage.set_title('New Review or Continue an Old One')
        choicePage.set_logo(self.logo)
        choiceGroup = gtk.VBox()
        choiceGroup.set_spacing(3)

        choiceLabel = gtk.Label('You can choose either to create a new review'
                ' from one of the installed CheckList templates or continue'
                ' a saved review that you select from your files.')
        choiceLabel.set_line_wrap(True)
        choiceGroup.add(choiceLabel)

        newSelector = gtk.RadioButton(None, 'Start a new review')
        loadSelector = gtk.RadioButton(newSelector, 'Load a saved review')
        choiceGroup.add(newSelector)
        choiceGroup.add(loadSelector)

        choicePage.append_item('', choiceGroup, '')
        choicePage.connect('next', self.choice_next, newSelector)
        self.druidWidget.add(choicePage)

    def build_selector(self, checklists):
        '''Creates pages for selecting a new checklist.

        Arguments:
        :checklists: list of checklists we can instantiate.
        '''
        selectorPage = gnome.ui.DruidPageStandard()
        self.selectorPage = selectorPage
        selectorPage.set_title('Select the Checklist to start')
        selectorPage.set_logo(self.logo)
        selectorGroup = gtk.VBox()
        
        selectorLabel = gtk.Label("Please select the type of review you wish"
                " to start from the following list.  If you don't see the"
                " type of review you want to create it means no one has"
                " taken the time to write a checklist definition for it yet."
                " Please consider contributing one if that's the case.")
        selectorLabel.set_line_wrap(True)
        selectorGroup.add(selectorLabel)
        
        # Create a selection menu to choose from the available checklists
        checkStore = gtk.ListStore(gobject.TYPE_STRING,
                gobject.TYPE_STRING,
                gobject.TYPE_STRING)
        for filename in checklists:
            summary = None
            name = None
            # Set up a stream reader for the checklist file.
            try:
                checkReader = libxml2.newTextReaderFilename(filename)
            except:
                print '%s was not a CheckList file' % (filename)
                continue
            
            # Read in the summary and name for the checklist
            status = checkReader.Read()
            while status == 1:
                if (checkReader.LocalName() == 'checklist' and
                        checkReader.NodeType() == 1):
                    name = checkReader.GetAttribute('name')
                elif checkReader.LocalName() == 'summary':
                    status = checkReader.Read()     # Get the text element
                    if status == 1:
                        summary = checkReader.Value()
                    break
                status = checkReader.Read()
            
            if not (summary and name):
                print 'Unable to get a summary and name from %s' % (filename)
                continue
            
            # Enter the information into the checkStore
            checkIter = checkStore.append(None)
            checkStore.set(checkIter, self.__FILENAME, filename,
                    self.__CHECKNAME, name,
                    self.__CHECKSUMMARY, summary)
                   
        checkList = gtk.TreeView(checkStore)
        self.selectorSelection = checkList.get_selection()
        self.selectorSelection.set_mode(gtk.SELECTION_SINGLE)

        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Name', renderer, text=1)
        checkList.append_column(column)

        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Summary', renderer, text=2)
        checkList.append_column(column)

        selectorGroup.add(checkList)
        selectorPage.append_item('',selectorGroup,'')

        selectorPage.connect('next', self.selector_next)

        self.druidWidget.add(selectorPage)

        # Double-clicking the row is the same as selecting next.
        checkList.connect('row-activated',
                lambda self, selector, column, druid: druid.next.clicked(),
                self.druidWidget)

    def build_loader(self):
        '''Create pages to load a saved CheckList.
        
        '''
        loaderPage = gnome.ui.DruidPageStandard()
        self.loaderPage = loaderPage
        loaderPage.set_title('Select the Review to load')
        loaderPage.set_logo(self.logo)
        loadGroup = gtk.VBox()
        loadLabel = gtk.Label('Please enter the file containing the review'
                ' you want to continue working on.')
        loadGroup.add(loadLabel)
        
        ### FIXME: pygtk-2.4 has an embeddable file chooser widget.
        # For now have a file entry box and a Browse... button.
        # When I have pygtk-2.4 installed, I'll use the FileChooserWidget
        # instead.
        browseBar = gtk.HBox()
        browseEntry = gtk.Entry()
        browseButton = gtk.Button('Browse...')
        browseBar.add(browseEntry)
        browseBar.add(browseButton)
        loadGroup.add(browseBar)
        loaderPage.append_item('',loadGroup,'')

        # Clicking the browse button pops up the FileSelect dialog.
        browseButton.connect('clicked', self.popup_file_selector)

        # Save the Entry so we can get information from it later.
        self.browseEntry = browseEntry

        loaderPage.connect('back', self.loader_back)
        loaderPage.connect('next', self.loader_next)
        self.druidWidget.add(loaderPage)
       
    def build_properties(self):
        '''

        '''
        propertiesPage = gnome.ui.DruidPageStandard()
        self.propertiesPage =  propertiesPage
        propertiesPage.set_title('Set Checklist Properties')
        propertiesPage.set_logo(self.logo)
        
        propForm = PropertiesView()
        self.propertiesPage.append_item('', propForm, '')
      
        self.druidWidget.add(propertiesPage)

        # Rebuild the properties entry widget as it may be using a new
        # checklist.
        propertiesPage.connect('prepare', self.properties_create, propForm)

    def build_end(self):
        '''
        '''
        endPage = gnome.ui.DruidPageEdge(gnome.ui.EDGE_FINISH)
        endPage.set_title('Ready to Begin')
        endPage.set_logo(self.app.logo)
        endPage.set_text('You have finished entering the required information.'
                ' Press Apply if the following summary is correct.')
        self.druidWidget.add(endPage)
        endPage.connect('finish', self.finish)

    def properties_create(self, page, druid, propForm):
        '''

        '''
        propForm.set_model(self.newList.properties)
        propForm.show()

    def finish(self, page, druid):
        '''

        '''
        try:
            self.app.checklist.destroy()
        except AttributeError:
            # No problems as long as checklist no longer exists.
            pass
        self.app.checklist = self.newList

        ### FIXME: The following might be better done in QAReviewer but first
        # We need to figure out how to notify QA Reviewer that the checklist
        # has changed.  Probably the easiest way is to set the checklist to
        # be a GProperty in QA Reviewer.  But that might mean some recoding
        # of QA Reviewer.  I think I'll wait for pygtk-2.4.0 which might
        # allow us to do this without serious hardship.
        self.app.checkView.set_model(self.app.checklist)
        self.app.checkView.show()

        ### FIXME: Need to substitute checklist.function loading instead.
        from srpmqa import SRPMQA
        qamenu = SRPMQA(self.app)
        self.app.QAMenuItem.set_submenu(qamenu)
        qamenu.show_all()

        self.app.reviewView.set_model(self.app.checklist)
        self.app.reviewView.show()

        self.destroy()

    #
    # Navigation Callbacks
    #
    
    def properties_back(self, page, druid):
        '''

        '''
        druid.set_page(self.propBackPage)
        return True

    def loader_next(self, page, druid):
        '''Check that the filename we get from the user is a valid checklist.

        Arguments:
        :page: Druid page we're on.
        :druid: Druid widget.
        '''
        try:
            self.newList = CheckList(self.browseEntry.get_text())
        except error.InvalidChecklist, ex_instance:
            errorDialog = gtk.MessageDialog(self.app.ReviewerWindow,
                    gtk.DIALOG_DESTROY_WITH_PARENT,
                    gtk.MESSAGE_WARNING,
                    gtk.BUTTONS_CLOSE,
                    'We were unable to load the specified file.'
                    ' The error given was:\n' + ex_instance.msg +
                    '\n\nPlease select another file.')
            errorDialog.set_title('Unable to load file')
            errorDialog.set_default_response(gtk.RESPONSE_CLOSE)
            response = errorDialog.run()
            errorDialog.destroy()
            #self.browseEntry.set_text('')
            druid.set_page(page)
            return True

        druid.set_page(self.propertiesPage)
        self.propBackPage = page
        return True

    def selector_next(self, page, druid):
        '''Moves from the selector page to the next page.

        Arguments:
        :page: Druid page we're on.
        :druid: Druid widget.
        '''
        (model, selectedRow) = self.selectorSelection.get_selected()
        try:
            if not selectedRow:
                raise error.InvalidChecklist, 'No checklist file was selected.'
            self.newList = CheckList(model.get_value(selectedRow,
                self.__FILENAME))
        except error.InvalidChecklist, ex_instance:
            errorDialog = gtk.MessageDialog(self.app.ReviewerWindow,
                    gtk.DIALOG_DESTROY_WITH_PARENT,
                    gtk.MESSAGE_WARNING,
                    gtk.BUTTONS_CLOSE,
                    'We were unable to load the specified file.'
                    ' The following error given was:\n' + ex_instance.msg +
                    '\n\nPlease select another file.')
            errorDialog.set_title('Unable to load file')
            errorDialog.set_default_response(gtk.RESPONSE_CLOSE)
            response = errorDialog.run()
            errorDialog.destroy()
            druid.set_page(page)
            return True

        druid.set_page(self.propertiesPage)
        self.propBackPage = page
        return True

    def choice_next(self, page, druid, newSelectorButton):
        '''Decide if we want a new checklist or load an old one.

        Arguments:
        :page: page we are loading from.
        :druid: druid we are workign with.
        :newSelectorButton: new review selector button.

        '''
        if newSelectorButton.get_active():
            # Change to the new review page
            druid.set_page(self.selectorPage)
            return True
        else:
            # Change to the load page
            druid.set_page(self.loaderPage)
            return True

    def loader_back(self, page, druid):
        '''Go back from the load page to the selector page.
        
        Arguments:
        :page: page we are loading from.
        :druid: druid we are working with.
        '''
        if self.mode == START:
            druid.set_page(self.choicePage)
            return True
        return False

    def disable_back(self, page, druid, backPage):
        '''Disable the back button for the page.
        '''
        druid.set_page(backPage)
        druid.set_buttons_sensitive(False, True, True, True)
        return True
    #
    # Other callbacks
    #
   
    ### FIXME: This can be replaced with thepygtk-2.4 FileSelector
    def popup_file_selector(self, button):
        '''Open a saved review
        
        Arguments:
        :button: The button which was clicked to bring up this dialog.
        '''
        fileSelect = gtk.FileSelection(title='Select the checklist file to load.')
        if (os.path.isdir(self.app.lastSaveFileDir) and
                os.access(self.app.lastSaveFileDir, os.R_OK|os.X_OK)):
            fileSelect.set_filename(self.app.lastSaveFileDir)

        filename = None
        response = fileSelect.run()
        try:
            if response == gtk.RESPONSE_OK:
                filename = fileSelect.get_filename()
        finally:
            fileSelect.destroy()
            del fileSelect

        if filename:
            self.app.lastSaveFileDir = os.path.dirname(filename)+'/'
            self.browseEntry.set_text(filename)

    def close_druid(self, druidObject):
        druidObject.get_parent_window().destroy()
