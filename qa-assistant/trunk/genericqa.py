# File: GenericQA.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 15 April, 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
"""Menu Items and actions for a Generic QA checklist
"""
__revision__ = "$Rev$"

import os
import gtk
import error

class GenericQA(gtk.Menu):

    def __init__(self, app):
        gtk.Menu.__init__(self)
        self.app = app
        addItem = gtk.MenuItem('Add Check_list Item')
        addItem.connect('activate', self.add_item_to_checklist_callback)
        self.append(addItem)
        
        self.append(gtk.SeparatorMenuItem())

        publishItem = gtk.MenuItem('_Publish to file')
        publishItem.connect('activate', self.publish_callback)
        self.append(publishItem)

    def publish_callback(self, callingMenu):
        """Publish a review to a file."""
 
        # Check that the review is in a completed state
        if self.app.reviewView.resolution.get_text() == 'Incomplete Review':
            msgDialog = gtk.MessageDialog(self.app.ReviewerWindow,
                    gtk.DIALOG_DESTROY_WITH_PARENT,
                    gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                    'You have not checked all items in the checklist so the review is incomplete.  Are you sure you want to submit a review based on the current work?')
            msgDialog.set_title('Incomplete review: submit anyway?')
            msgDialog.set_default_response(gtk.RESPONSE_NO)
            response = msgDialog.run()
            msgDialog.destroy()
            if (response == gtk.RESPONSE_NO or response == gtk.RESPONSE_NONE
                    or response == gtk.RESPONSE_DELETE_EVENT):
                return
        
        # File select dialog for use in file selecting callbacks.
        fileSelect = gtk.FileSelection(title='Select a file to publish the review into')
        if (os.path.isdir(self.app.properties.lastReviewDir) and
                os.access(self.app.properties.lastReviewDir, os.R_OK|os.X_OK)):
            fileSelect.set_filename(self.app.properties.lastReviewDir)

        filename = None
        response = fileSelect.run()
        try:
            if response == gtk.RESPONSE_OK:
                filename = fileSelect.get_filename()
        finally:
            fileSelect.destroy()
            del fileSelect

        if filename:
            self.app.properties.lastReviewDir = os.path.dirname(filename)+'/'
            try:
                self.app.reviewView.publish(filename)
            except IOError, msg:
                ### FIXME: MSG Dialog that we could not publish the review
                pass

    def add_item_to_checklist_callback(self, callingMenu):
        """Adds a checklist entry to the checklist.
        
        Sometimes there's something wrong with a product undergoing QA that
        isn't on the checklist.  Using this action allows you to add an entry
        to the checklist you are currently filling out.
        """

        # Dialog to prompt the user for the information
        newItemDialog = gtk.Dialog('New checklist item',
                self.app.ReviewerWindow, 0, ('Add item', gtk.RESPONSE_OK,
                    gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        newItemDialog.set_default_response(gtk.RESPONSE_OK)
        table = gtk.Table(3, 2, False)
        table.attach(gtk.Label('Summary:'), 0,1, 0,1)
        table.attach(gtk.Label('Initial Resolution:'), 0,1, 1,2)
        table.attach(gtk.Label('Output:'), 0,1, 2,3)
        summaryEntry = gtk.Entry()
        resMenu = gtk.Menu()
        resList = ('Pass', 'Fail', 'Non-Blocker')
        outputList = {}
        for res in resList:
            outputList[res] = None
            resMenu.append(gtk.MenuItem(res))
        resEntry = gtk.OptionMenu()
        resEntry.set_menu(resMenu)
        resEntry.set_history(1)
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
                    msgDialog = gtk.MessageDialog(self.app.ReviewerWindow,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
                            'You must enter a value for the Summary')
                    msgDialog.set_title('Invalid summary')
                    msgDialog.set_default_response(gtk.RESPONSE_CLOSE)
                    response = msgDialog.run()
                    msgDialog.destroy()
                    continue
                res = resEntry.get_history()
                res = resList[res]
                output = outputEntry.get_text()
                output = self.app.checklist.pangoize_output(res, output)
                outputList[res] = output

                try:
                    self.app.checklist.add_entry(summary, desc=None,
                            item=True,
                            display=True,
                            resolution=res,
                            output=output,
                            resList=resList,
                            outputList=outputList)
                except error.DuplicateItem:
                    msgDialog = gtk.MessageDialog(self.app.ReviewerWindow,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
                            'The Summary must not be the same as any other existing entry.  Please consider renaming the new checklist item or using the existing entry for this review.')
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
