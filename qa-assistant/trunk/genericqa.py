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

class GenericQA(gtk.Menu):

    def __init__(self, app):
        gtk.Menu.__init__(self)
        self.app = app
        addItem = gtk.MenuItem('Add Checklist _Item')
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
            response = msgDialog.run()
            msgDialog.destroy()
            if response == gtk.RESPONSE_NO:
                return
        
        # File select dialog for use in file selecting callbacks.
        fileSelect = gtk.FileSelection(title='Select a file to publish the review into')
        if (os.path.isdir(self.app.properties.lastSRPMDir) and
                os.access(self.app.properties.lastSRPMDir, os.R_OK|os.X_OK)):
            fileSelect.set_filename(self.app.properties.lastReviewDir)
        response = fileSelect.run()
        try:
            if response == gtk.RESPONSE_OK:
                filename = fileSelect.get_filename()
                self.app.properties.lastReviewDir = os.path.dirname(filename)+'/'
                self.app.reviewView.publish(fileSelect.get_filename())
        finally:
            fileSelect.destroy()
            del fileSelect

    def add_item_to_checklist_callback(self, callingMenu):
        """ """
        # Create a checklist item that has DISPLAY [yes]
        # RESOLUTION (Needs-Reviewing)
        # OUTPUT (None)
        # OUTPUTLIST (all)
        # RESOLUTIONLIST (all)
        # If no category "My Items", create
        # Append new item to My Items.
        msg = """This item will allow you to add your own checklist item to the current review.  Since the checklist authors could have missed an entry that you know to be wrong with the program, this is desirable.  For instance: "Program does not call my dog:  gdogcaller fails to make my dog come when I run it which is what I assume such a program to do.
        
I consider this a must have feature.  QA Assistant cannot be considered complete without this.  However, it is still possible to perform without this and it entails some non-trivial coding so it is a low priority necessity."""
        self.app.not_yet_implemented(msg)
        pass
