# File: review.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 26 March 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
"""A review object with methods to display and publish itself.
"""
__revision__ = "$Rev$"

import gtk
import gconf
import gobject
try:
    import textwrap
except ImportError:
    try:
        from optik import textwrap
    except ImportError:
        from optparse import textwrap

from qaglobals import *
import checklist
import gpg
import error

class Review(gtk.VBox):
    '''Widget to display and print a checklist.
    
    The review widget takes a checklist and displays it on the screen in the
    form it will be printed as.  Also can print the checklist.
    '''

    def __init__(self, treeStore=None):
        ''' Create a new Review object. 
        
        Attributes:
        :treeStore: A gtk.TreeModel to operate on.
        '''
        if treeStore:
            assert isinstance(treeStore, checklist.CheckList), \
                    '%s is not a CheckList type' % (treeStore)
        gtk.VBox.__init__(self)

        # Create the textwrap object for use by the publish method
        self.textwrap = textwrap.TextWrapper(initial_indent='* ',
                subsequent_indent='  ')

        # Create the gconf client to retrieve the gpg options
        self.gconfClient = gconf.client_get_default()
        self.gconfClient.add_dir(GCONFPREFIX, gconf.CLIENT_PRELOAD_NONE)

        # Create the widgets:
        self.reviewBoxes = {}

        self.header = gtk.Label()
        self.add(self.header)

        self.reviewTitles = {}
        for titles in ('Pass', 'Fail', 'Non-Blocker', 'Notes'):
            self.reviewTitles[titles] = gtk.Label()
            self.reviewTitles[titles].set_property('xalign', 0.0)
            self.add(self.reviewTitles[titles])
        self.reviewTitles['Pass'].set_text('Good:')
        self.reviewTitles['Fail'].set_text('Needswork:')
        self.reviewTitles['Non-Blocker'].set_text('Minor:')
        self.reviewTitles['Notes'].set_text('Notes:')

        self.footer = gtk.Label()
        self.add(self.footer)

        # Set display properties on the widgets
        self.header.set_selectable(True)
        self.footer.set_selectable(True)
        self.set_property('homogeneous', False)
        self.header.set_property('xalign', 0.0)
        self.footer.set_property('xalign', 0.0)

        # Copy data from the checklist into internal structures and add to
        # our display.
        if treeStore:
            self.set_model(treeStore)
        
    def show(self):
        """Display the new widget"""
        self.show_all()

    def publish(self, filename):
        '''Write the review to a file.

        Arguments:
        :filename: filename to write to.

        Write the review out to a file.
        '''

        if not self.checklist.properties.requirementsMet:
            # Popup a dialog to finish entering properties
            requireDialog = gtk.MessageDialog(None,
                    gtk.DIALOG_DESTROY_WITH_PARENT,
                    gtk.MESSAGE_WARNING,
                    gtk.BUTTONS_CLOSE,
                    'There are several properties in this checklist that are'
                    ' required.  A review cannot be printed until those'
                    ' entries are filled in.  Please be sure you have entered'
                    ' each property which is displayed in italics in the'
                    ' Edit::Properties menu and then try to publish again.')
            requireDialog.set_title('Enter All Required Properties')
            requireDialog.set_default_response(gtk.RESPONSE_CLOSE)
            requireDialog.run()
            requireDialog.destroy()
            return
        
        outBuf = self.checklist.functions.header() + '\n'
        # Loop through the review areas:
        for box in ('Pass', 'Fail', 'Non-Blocker', 'Notes'):
            reviewBox = self.reviewBoxes[box]
            tempOutBuf = '\n'
            # Add items from this review category to the output buffer.
            for entryLabel in reviewBox.get_children():
                value = entryLabel.get_text()
                if value:
                    value = self.checklist.unpangoize_output(value)
                    tempOutBuf += self.textwrap.fill(value) + '\n'
            if tempOutBuf:
                outBuf += self.reviewTitles[box].get_text() + tempOutBuf + '\n'

        # Sign the review if the user has decided to
        key = GCONFPREFIX + '/user/use-gpg'
        try:
            sign = self.gconfClient.get_bool(key)
        except gobject.GError:
            sign = self.gconfClient.get_default_from_schema(key).get_bool()
        if sign:
            key = GCONFPREFIX + '/user/gpg-identity'
            try:
                gpgId = self.gconfClient.get_string(key)
            except gobject.GError:
                # If no ID is set, we'll use whatever gpg considers the
                # default.
                gpgId = None

            key = GCONFPREFIX + '/files/gpg-path'
            try:
                gpgPath = self.gconfClient.get_string(key)
            except gobject.GError:
                gpgPath = self.gconfClient.get_default_from_schema(key).get_string()
            reenterPassphrase = False
            while True:
                passphrase = gpg.get_passphrase(gpgId, reenterPassphrase)
                if passphrase == None:
                    break
                try:
                    outBuf = gpg.sign_buffer(outBuf, gpgId, gpgPath, passphrase)
                except error.BadPassphrase:
                    reenterPassphrase = True
                except error.NoSecretKey:
                    errorDialog = gtk.MessageDialog(None,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            gtk.MESSAGE_WARNING,
                            gtk.BUTTONS_CLOSE,
                            'No secret key was found for that user ID.  Please'
                            ' go to the Edit::Preferences Menu.  Select'
                            ' another id to sign with in the Preferences'
                            ' Dialog.')
                    errorDialog.set_title('No Signing Key')
                    errorDialog.set_default_response(gtk.RESPONSE_CLOSE)
                    response = errorDialog.run()
                    errorDialog.destroy()
                    return
                except error.NoOut:
                    errorDialog = gtk.MessageDialog(None,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            gtk.MESSAGE_WARNING,
                            gtk.BUTTONS_CLOSE,
                            'No output was created by GPG when trying to'
                            ' sign the review.  This is likely a problem'
                            ' with the way gpg is setup.  Please take a look'
                            ' in the Edit::Preferences menu and see if there'
                            ' are any errors there.  If not, you may want to'
                            ' disable automatic gpg signing and publish your'
                            ' review.  Then sign it manually using your gpg'
                            ' number.')
                    errorDialog.set_title('No Output Created')
                    errorDialog.set_default_response(gtk.RESPONSE_CLOSE)
                    response = errorDialog.run()
                    errorDialog.destroy()
                    return
                except error.NotGPGCompatible:
                    errorDialog = gtk.MessageDialog(None,
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            gtk.MESSAGE_WARNING,
                            gtk.BUTTONS_CLOSE,
                            'The program specified in the Preferences'
                            ' dialog does not appear to take the same'
                            ' commandline arguments as gpg.  Please specify'
                            ' a new program in the Preferences that is either'
                            ' gpg or something that is a dropin replacement'
                            ' for it.')
                    errorDialog.set_title('Invalid GPG program specified')
                    errorDialog.set_default_response(gtk.RESPONSE_CLOSE)
                    response = errorDialog.run()
                    errorDialog.destroy()
                    return
                else:
                    # Success!
                    break

        # Output review
        outfile = file(filename, 'w')
        outfile.writelines(outBuf)
        outfile.close()

    def submit(self):
        '''Submit the output to a ticketting system.

        This needs to be broken up into two parts.  Most of it will be done by
        the QAreviewer program.  Only formatting the output will be done here.
        I think I can see where we might be able to just do this with the
        publish method.  But we'll need to change it to write to an internal
        buffer or something.
        '''
        pass

    def set_model(self, treeStore):
        '''Set a new model for the Review to get data from.

        Attributes:
        :treeStore: The model for which we are writing the Review.

        This method sets a new treemodel for the Review.
        '''
        self.checklist = treeStore
        treeStore.connect('row-changed', self.__update_data)
        self.__sync_checklist()

    def __sync_checklist(self):
        ''' Sync the Review to a new checklist model.

        This loads the checklist data into the internal data structures and
        then adds them to the displayBoxes.
        '''
        treeStore = self.checklist
        self.entries = {} # Keys to transform summary -> resolution/entry order
        self.displayList = {} # res/entry order -> gtk.Label()
        lastEntry = 0
        summaries = treeStore.entries.keys()
        for summary in summaries:
            treeIter = treeStore.entries[summary]
            if treeStore.get_value(treeIter, checklist.DISPLAY):
                key  = (treeStore.get_value(treeIter, checklist.RESOLUTION),
                        lastEntry)
                value = gtk.Label(treeStore.get_value(treeIter,
                    checklist.OUTPUT))
                value.set_use_markup(True)
                value.set_line_wrap(True)
                value.set_selectable(True)
                value.set_property('xalign', 0.0)
                self.displayList[key] = value
                self.entries[summary] = key
                lastEntry += 1

        self.lastEntry = lastEntry
        # Clear out the Boxes that hold review items
        try:
            for box in self.reviewBoxes.values():
                self.remove(box)
        except AttributeError:
            # As long as the reviewBoxes do not exist, it's safe to continue.
            pass
        for box in ('Pass', 'Fail', 'Non-Blocker', 'Notes'):
            self.reviewBoxes[box] = gtk.VBox()
        
        # Fill each display list
        ### FIXME: Figure out whether we want to hide the display *Box's before
        # doing this.
        for entry in self.displayList.iteritems():
            res = entry[0][0]
            if res == 'Needs-Reviewing' or res == 'Not-Applicable':
                self.reviewBoxes['Notes'].add(entry[1])
            else:
                self.reviewBoxes[res].add(entry[1])

        pos = 2
        for box in ('Pass', 'Fail', 'Non-Blocker', 'Notes'):
            self.add_with_properties(self.reviewBoxes[box], 'position', pos)
            pos += 2

    def __update_data(self, treeStore, path, updateIter):
        '''Update internal list from treeStore when treeStore is changed.
        
        Attributes:
        :treeStore: The CheckList we're working with.
        :path: The path to the value that was changed.
        :updateIter: Iter to the changed Row.
        '''
        # row-changed gets called once for each item that is updated, even
        # when there's a group.  So we have to wait until we get a proper
        # summary (our key value) when we add the entry to the list
        summary = treeStore.get_value(updateIter, checklist.SUMMARY)
        res = treeStore.get_value(updateIter, checklist.RESOLUTION)
        output = treeStore.get_value(updateIter, checklist.OUTPUT) or ''
        if not (summary and res and len(path) > 1):
            # 1) Don't care about Categories (toplevel items)
            # 2) Items that don't have summaries and resolutions yet are in
            #    the process of being added.
            return

        summary = summary.lower()
        if self.entries.has_key(summary):
            # Update an old item
            key = self.entries[summary]
            if not treeStore.get_value(updateIter, checklist.DISPLAY):
                # No longer need to display it
                key = self.entries[summary]
                if key[0] == 'Needs-Reviewing' or key[0] == 'Not-Applicable':
                    self.reviewBoxes['Notes'].remove(self.displayList[key])
                else:
                    self.reviewBoxes[key[0]].remove(self.displayList[key])
                del self.displayList[key]
                del self.entries[summary]
                return

            # Save the old label
            label = self.displayList[key]
            if key[0] != res:
                # Change the key
                if key[0] == 'Needs-Reviewing' or key[0] == 'Not-Applicable':
                    self.reviewBoxes['Notes'].remove(self.displayList[key])
                else:
                    self.reviewBoxes[key[0]].remove(self.displayList[key])
                del self.displayList[key]
                key = (res, key[1])
                self.entries[summary] = key
                self.displayList[key] = label
                if key[0] == 'Needs-Reviewing' or key[0] == 'Not-Applicable':
                    self.reviewBoxes['Notes'].add(label)
                else:
                    self.reviewBoxes[key[0]].add(label)
            # Change output
            label.set_markup(output)
        else:
            # New item
            if treeStore.get_value(updateIter, checklist.DISPLAY):
                key = (res, self.lastEntry)
                self.entries[summary] = key
                label = gtk.Label(output)
                label.set_use_markup(True)
                label.set_property('xalign', 0.0)
                label.set_selectable(True)
                label.set_line_wrap(True)
                self.displayList[key] = label
                if key[0] == 'Needs-Reviewing' or key[0] == 'Not-Applicable':
                    self.reviewBoxes['Notes'].add(label)
                else:
                    self.reviewBoxes[key[0]].add(label)
                label.show()
                self.lastEntry += 1
