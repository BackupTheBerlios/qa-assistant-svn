# File: functions.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 16 Fed 2005
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
'''
'''
__revision__ = '$Rev$'

import os
import gtk
import gnome

import error
import qaglobals

class BaseQAFunctions(object):
    '''

    '''
    # Functions that are created by the checklist.
    def __init__(self, checklist):
        self.checklist = checklist
        self.QAMenu = None
        
    # Output functions
    def header(self):
        '''Print out a header on a review.

        Override this function if you wish to print an alternate heading
        on the review.
        '''
        return self.checklist.resolution
    
    def footer(self):
        return ('Created in ' 
                + qaglobals.HUMANPROGRAMNAME
                + ' ' + qaglobals.VERSION)
        
    #
    # Menu functions
    #
    def get_ui(self, app):
        '''Returns a uimanager ui definition and actiongroup definition.
        
        The functions interface needs to return a uimanaged set of menus and
        toolbars so the app can merge and unmerge them when new checklists are
        opened.
        '''

        uiElements = '''<ui>
            <menubar name="MainMenu">
              <menu action="QAActions">
                <menuitem action="AddChecklistItem" position="top"/>
                <separator/>
                <menuitem action="PublishToFile" position="bot"/>
              </menu>
            </menubar>
            <toolbar name="MainToolBar">
              <toolitem action="PublishToFile"/>
            </toolbar>
            </ui>
            '''
        uiActions = (
                ('AddChecklistItem', None, '_Add Checklist Item', '<control>i',
                    'Add a checklist item to fill in with extra notes',
                    self.add_item_cb),
                ('PublishToFile', None, '_Publish to file', '<control>u',
                    'Publish the review from the checklist to a file',
                    self.publish_cb))
        actiongroup = gtk.ActionGroup('QA Menu')
        actiongroup.add_actions(uiActions, app)
        return [(actiongroup, uiElements)]

    def add_item_cb(self, action, app, *extra):
        '''Adds a checklist entry to the checklist.
        
        Sometimes there's something wrong with a product undergoing QA that
        isn't on the checklist.  Using this action allows you to add an entry
        to the checklist you are currently filling out.
        '''

        # Dialog to prompt the user for the information
        newItemDialog = gtk.Dialog('New checklist item',
                app.ReviewerWindow,
                0, ('Add item', gtk.RESPONSE_OK,
                    gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        newItemDialog.set_default_response(gtk.RESPONSE_OK)
        table = gtk.Table(3, 2, False)
        table.attach(gtk.Label('Summary:'), 0,1, 0,1)
        table.attach(gtk.Label('Initial Resolution:'), 0,1, 1,2)
        table.attach(gtk.Label('Output:'), 0,1, 2,3)
        summaryEntry = gtk.Entry()
        resEntry = gtk.combo_box_new_text()
        resList = ('Pass', 'Fail', 'Non-Blocker')
        outputList = {}
        for res in resList:
            outputList[res] = ''
            resEntry.append_text(res)
        resEntry.set_active(1)
        outputEntry = gtk.Entry()
        table.attach(summaryEntry, 1,2, 0,1)
        table.attach(resEntry, 1,2, 1,2)
        table.attach(outputEntry, 1,2, 2,3)
        
        newItemDialog.vbox.add(table)
        newItemDialog.show_all()

        while True:
            response = newItemDialog.run()
            if response == gtk.RESPONSE_OK:
                # Check that the summary entry is okay.
                summary = summaryEntry.get_text().strip()
                if len(summary) <= 0:
                    msgDialog = gtk.MessageDialog(app.ReviewerWindow,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
                            'You must enter a value for the Summary')
                    msgDialog.set_title('Invalid summary')
                    msgDialog.set_default_response(gtk.RESPONSE_CLOSE)
                    response = msgDialog.run()
                    msgDialog.destroy()
                    continue
                resIndex = resEntry.get_active()
                res = resList[resIndex]
                output = outputEntry.get_text()
                outputList[res] = output

                try:
                    self.checklist.add_entry(summary, desc=None,
                            item=True,
                            display=True,
                            resolution=res,
                            output=output,
                            resList=resList,
                            outputList=outputList)
                except error.DuplicateItem:
                    msgDialog = gtk.MessageDialog(app.ReviewerWindow,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
                            'The Summary must not be the same as any other'
                            ' existing entry.  Please consider renaming the'
                            ' new checklist item or using the existing entry'
                            ' for this review.')
                    msgDialog.set_title('Invalid summary')
                    msgDialog.set_default_response(gtk.RESPONSE_CLOSE)
                    response = msgDialog.run()
                    msgDialog.destroy()
                    continue
                else:
                    break
            else:
                # User decided not to write a new entry
                break
        newItemDialog.destroy()

    def publish_cb(self, action, app, *extra):
        '''Publish a review to a file.'''
        # Check that the review is in a completed state
        if self.checklist.resolution == 'Needs-Reviewing':
            msgDialog = gtk.MessageDialog(app.ReviewerWindow,
                    gtk.DIALOG_DESTROY_WITH_PARENT,
                    gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                    'You have not checked all items in the checklist so the'
                    ' review is incomplete.  Are you sure you want to submit'
                    ' a review based on the current work?')
            msgDialog.set_title('Incomplete review: submit anyway?')
            msgDialog.set_default_response(gtk.RESPONSE_NO)
            response = msgDialog.run()
            msgDialog.destroy()
            if (response == gtk.RESPONSE_NO or response == gtk.RESPONSE_NONE
                    or response == gtk.RESPONSE_DELETE_EVENT):
                return

        # Select the file to publish a review into
        fileSelect = gtk.FileSelection(
                title = 'Select a file to publish the review into')
        if (os.path.isdir(qaglobals.lastReviewDir) and
                os.access(qaglobals.lastReviewDir, os.R_OK|os.X_OK)):
            fileSelect.set_filename(qaglobals.lastReviewDir)

        filename = None
        response = fileSelect.run()
        try:
            if response == gtk.RESPONSE_OK:
                filename = fileSelect.get_filename()
        finally:
            fileSelect.destroy()
            del fileSelect

        if filename:
            qaglobals.lastReviewDir = os.path.dirname(filename) + os.path.sep
            try:
                app.reviewView.publish(filename)
            except IOError, msg:
                msgDialog = gtk.MessageDialog(app.ReviewerWindow,
                        gtk.DIALOG_DESTROY_WITH_PARENT,
                        gtk.MESSAGE_QUESTION, gtk.BUTTONS_CLOSE,
                        'The location you selected is not a valid place to'
                        ' save the review.  This could be because you don\'t'
                        ' have permission to write files there, lack of disk'
                        ' space, or some other problem.  Please select'
                        ' another directory to save into.')
                msgDialog.set_title('Not a Writable Location')
                msgDialog.set_default_response(gtk.RESPONSE_NO)
                response = msgDialog.run()
                msgDialog.destroy()
                return
