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

import checklist

class GenericQA(gtk.Menu):

    def __init__(self, app):
        gtk.Menu.__init__(self)
        self.app = app
        self.customItemsPath = None
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
        resMenu.append(gtk.MenuItem('Pass'))
        resMenu.append(gtk.MenuItem('Fail'))
        resMenu.append(gtk.MenuItem('Non-Blocker'))
        resEntry = gtk.OptionMenu()
        resEntry.set_menu(resMenu)
        resEntry.set_history(1)
        outputEntry = gtk.Entry()
        table.attach(summaryEntry, 1,2, 0,1)
        table.attach(resEntry, 1,2, 1,2)
        table.attach(outputEntry, 1,2, 2,3)
        
        newItemDialog.vbox.add(table)
        newItemDialog.show_all()

        while 1:
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
                if self.app.checklist.entries.has_key(summary):
                    msgDialog = gtk.MessageDialog(self.app.ReviewerWindow,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
                            'The Summary must not be the same as any other existing entry.  Please consider renaming the new checklist item or using the existing entry for this review.')
                    msgDialog.set_title('Invalid summary')
                    msgDialog.set_default_response(gtk.RESPONSE_CLOSE)
                    response = msgDialog.run()
                    msgDialog.destroy()
                    continue

                res = resEntry.get_history()
                if res == 0:
                    res = 'Pass'
                elif res == 1:
                    res = 'Fail'
                elif res == 2:
                    res = 'Non-Blocker'
                output = outputEntry.get_text()
                output = self.app.checklist.colorize_output(res, output)
                break
            else:
                # User decided not to write a new entry
                newItemDialog.destroy()
                return

        newItemDialog.destroy()
        if self.customItemsPath:
            iter = self.app.checklist.tree.get_iter(self.customItemsPath)
        else:
            # Create the 'Custom Checklist Items' category
            iter = self.app.checklist.tree.append(None)
            self.app.checklist.tree.set(iter,
                    checklist.SUMMARY, 'Custom Checklist Items',
                    checklist.ISITEM, False,
                    checklist.RESLIST, ['Needs-Reviewing', 'Pass', 'Fail'],
                    checklist.RESOLUTION, 'Needs-Reviewing',
                    checklist.OUTPUT, None,
                    checklist.OUTPUTLIST, {'Needs-Reviewing':None,
                                           'Pass':None, 'Fail':None},
                    checklist.DESC, '''Review items that you have comments on even though they aren't on the standard checklist.''')
            self.customItemsPath = self.app.checklist.tree.get_path(iter)
        
        resList = ['Needs-Reviewing', 'Pass', 'Fail', 'Non-Blocker', 'Not-Applicable']
        outputList = {}
        for name in resList:
            outputList[name] = None
        outputList[res] = output
        newItem = self.app.checklist.tree.append(iter)
        self.app.checklist.tree.set(newItem,
                checklist.DESC, None,
                checklist.ISITEM, True,
                checklist.DISPLAY, True,
                checklist.SUMMARY, summary,
                checklist.RESOLUTION, res,
                checklist.OUTPUT, output,
                checklist.RESLIST, resList,
                checklist.OUTPUTLIST, outputList)
        self.app.resolution_changed(None, res, newItem)
