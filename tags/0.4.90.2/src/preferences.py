# File: preferences.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 13 Oct, 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
'''A Dialog to take preference information.
'''
__revision__ = "$Rev$"

import os

import gtk
import gconf
import gobject

import gnomeglade
from qaconst import *
import error

import gpg

class Preferences(gnomeglade.Component):

    def __init__(self, gladeFile):
        '''Create a new preferences dialog to take in preferences.'''
        gnomeglade.Component.__init__(self, gladeFile, 'PreferencesDialog')

        # Initialize the gconf connection
        self.gconfClient = gconf.client_get_default()
        self.gconfClient.add_dir(GCONFPREFIX, gconf.CLIENT_PRELOAD_RECURSIVE)

        # Set initial colorbutton colors and callbacks for changing colors
        key = GCONFPREFIX + '/display/pass-color'
        try:
            self.PassColorButton.set_color(gtk.gdk.color_parse(
                self.gconfClient.get_string(key)))
        except (ValueError, gobject.GError):
            self.PassColorButton.set_color(gtk.gdk.color_parse(
                self.gconfClient.get_default_from_schema(key).get_string()))
        self.PassColorButton.connect('color-set', self.set_display_color,
                key)

        key = GCONFPREFIX + '/display/fail-color'
        try:
            self.FailColorButton.set_color(gtk.gdk.color_parse(
                self.gconfClient.get_string(key)))
        except (ValueError, gobject.GError):
            self.FailColorButton.set_color(gtk.gdk.color_parse(
                self.gconfClient.get_default_from_schema(key).get_string()))
        self.FailColorButton.connect('color-set', self.set_display_color,
                key)

        key = GCONFPREFIX + '/display/minor-color'
        try:
            self.MinorColorButton.set_color(gtk.gdk.color_parse(
                self.gconfClient.get_string(key)))
        except (ValueError, gobject.GError):
            self.MinorColorButton.set_color(gtk.gdk.color_parse(
                self.gconfClient.get_default_from_schema(key).get_string()))
        self.MinorColorButton.connect('color-set', self.set_display_color,
                key)

        key = GCONFPREFIX + '/display/notes-color'
        try:
            self.NotesColorButton.set_color(gtk.gdk.color_parse(
                self.gconfClient.get_string(key)))
        except (ValueError, gobject.GError):
            self.NotesColorButton.set_color(gtk.gdk.color_parse(
                self.gconfClient.get_default_from_schema(key).get_string()))
        self.NotesColorButton.connect('color-set', self.set_display_color,
                key)

        # Set up tooltip description preferences
        key = GCONFPREFIX + '/display/disable-checklist-descriptions'
        try:
            disableDesc = self.gconfClient.get_bool(key)
        except gobject.GError:
            disableDesc = (
                    self.gconfClient.get_default_from_schema(key).get_bool())
        if not disableDesc:
            self.DescriptionCheckButton.set_active(True)
        else:
            self.DescWaitSpin.set_sensitive(False)
            self.DescWaitLabelPre.set_sensitive(False)
            self.DescWaitLabelPost.set_sensitive(False)
        self.DescriptionCheckButton.connect('toggled',
                self.set_show_description)
        self.gconfClient.notify_add(key, self.toggle_desc_options)

        key = GCONFPREFIX + '/display/checklist-description-wait'
        try:
            descWait = self.gconfClient.get_int(key)
        except gobject.GError:
            descWait = self.gconfClient.get_default_from_schema(key).get_int()
        (spinMin, spinMax) = self.DescWaitSpin.get_range()
        if descWait < spinMin or descWait > spinMax:
            descWait = self.gconfClient.get_default_from_schema(key).get_int()
        self.DescWaitSpin.set_value(descWait)
        self.DescWaitSpin.connect('focus-out-event', self.set_desc_wait)
        
        # Set Review Output and setup callback for change
        key = GCONFPREFIX + '/display/no-auto-display'
        try:
            noAutoDisplay = self.gconfClient.get_bool(key)
        except gobject.GError:
            noAutoDisplay = (
                    self.gconfClient.get_default_from_schema(key).get-bool())
        if not noAutoDisplay:
            self.DisplayFailCheckButton.set_active(True)
        self.DisplayFailCheckButton.connect('toggled',
                self.set_display_on_fail)
        
        # Set the gpg options
        key = GCONFPREFIX + '/user/use-gpg'
        try:
            useGpg = self.gconfClient.get_bool(key)
        except gobject.GError:
            useGpg = self.gconfClient.get_default_from_schema(key).get_bool()
        if useGpg:
            self.SignCheckButton.set_active(True)
        else:
            self.GPGIdLabel.set_sensitive(False)
            self.GPGPathLabel.set_sensitive(False)
            self.GPGPathEntry.set_sensitive(False)
            self.SignIdCombo.set_sensitive(False)
        self.SignCheckButton.connect('toggled',
                self.set_use_gpg)
        self.gconfClient.notify_add(key, self.toggle_gpg_options)

        # path to gpg
        key = GCONFPREFIX + '/files/gpg-path'
        try:
            gpgPath = self.gconfClient.get_string(key)
        except gobject.GError:
            gpgPath = self.gconfClient.get_default_from_schema(key).get_string()
        self.GPGPathEntry.set_filename(gpgPath)
        self.GPGPathEntry.connect('changed', self.set_gpg_path)
        self.gconfClient.notify_add(key, self.change_gpg_path)

        # GPG identity
        self.create_gpg_ids_list(gpgPath)
        self.SignIdCombo.child.connect('focus-out-event',
                self.set_gpg_identity)
        self.SignIdCombo.connect('changed', self.set_gpg_identity)
        
        # Temporary directory for files
        key = GCONFPREFIX + '/files/user-state-dir'
        try:
            stateDir = self.gconfClient.get_string(key)
        except gobject.GError:
            stateDir = (
                    self.gconfClient.get_default_from_schema(key).get_string())
        self.StateDirEntry.set_filename(stateDir)
        self.StateDirEntry.connect('changed', self.set_state_dir)

        self.PreferencesOkButton.connect('clicked', self.close_win)
        self.PreferencesDialog.connect('destroy_event', self.close_win)
        self.PreferencesHelpButton.connect('clicked', self.NYI)

    #
    # Misc dialog methods
    #
        
    def NYI(self, *extra):
        print "Feature not yet implemented"

    def close_win(self, *extra):
        self.PreferencesDialog.destroy()
        del(self.xml)
        
    def create_gpg_ids_list(self, gpgPath):
        '''
        '''
        key = GCONFPREFIX + '/user/gpg-identity'
        try:
            gpgId = self.gconfClient.get_string(key)
        except gobject.GError:
            gpgId = None

        model = self.SignIdCombo.get_model()
        model.clear()
        if gpgId:
            model.append((gpgId,))
            self.SignIdCombo.set_active(0)

        try:
            gpgIdentities = gpg.list_secret_keys(gpgPath)
        except error.GPGError:
            # We are going to allow this to continue and check for validity
            # when we sign the review.  This is because the config might be
            # shared between different machines where the gpg program may or
            # may not work.
            return

        for identity in gpgIdentities:
            if gpgId != identity:
                model.append((identity,))

    #
    # Notify callbacks to change the GUI state
    #
    
    def change_gpg_path(self, client, connectId, entry, extra):
        '''Update the gpgID list when the gpg program is updated.
        '''
        if entry.value and entry.value.type == gconf.VALUE_STRING:
            self.create_gpg_ids_list(entry.value.get_string())
        
    def toggle_desc_options(self, client, connectId, entry, extra):
        '''Enable or disable settign the description options.

        '''
        if entry.value and entry.value.type == gconf.VALUE_BOOL:
            if entry.value.get_bool():
                self.DescWaitSpin.set_sensitive(False)
                self.DescWaitLabelPre.set_sensitive(False)
                self.DescWaitLabelPost.set_sensitive(False)
            else:
                self.DescWaitSpin.set_sensitive(True)
                self.DescWaitLabelPre.set_sensitive(True)
                self.DescWaitLabelPost.set_sensitive(True)

    def toggle_gpg_options(self, client, connectId, entry, extra):
        '''Enable or disable setting the gpg options.
        
        When use-gpg is set, we want to allow setting other gpg options.
        '''
        if entry.value and entry.value.type == gconf.VALUE_BOOL:
            if entry.value.get_bool():
                self.GPGPathEntry.set_sensitive(True)
                self.SignIdCombo.set_sensitive(True)
                self.GPGIdLabel.set_sensitive(True)
                self.GPGPathLabel.set_sensitive(True)
            else:
                self.GPGIdLabel.set_sensitive(False)
                self.GPGPathLabel.set_sensitive(False)
                self.GPGPathEntry.set_sensitive(False)
                self.SignIdCombo.set_sensitive(False)
    #
    # Callbacks to change values in GConf.
    #
    
    def set_display_color(self, button, key):
        '''Set the display color in gconf.

        Arguments:
        :button: gtk.ColorButton that has been set with the new color
        :key: gconf key to set witht he color information

        '''
        color = button.get_color()
        colorString = '#%02X%02X%02X' % (color.red/256, color.green/256, color.blue/256)
        self.gconfClient.set_string(key, colorString)

    def set_use_gpg(self, toggleButton):
        '''
        '''
        if toggleButton.get_active():
            self.gconfClient.set_bool(GCONFPREFIX + '/user/use-gpg', True)
        else:
            self.gconfClient.set_bool(GCONFPREFIX + '/user/use-gpg', False)
        
    def set_display_on_fail(self, toggleButton):
        '''
        '''
        if toggleButton.get_active():
            self.gconfClient.set_bool(GCONFPREFIX + '/display/no-auto-display',
                    False)
        else:
            self.gconfClient.set_bool(GCONFPREFIX + '/display/no-auto-display',
                    True)

    def set_show_description(self, toggleButton):
        '''
        '''
        if toggleButton.get_active():
            self.gconfClient.set_bool(GCONFPREFIX +
                    '/display/disable-checklist-descriptions', False)
        else:
            self.gconfClient.set_bool(GCONFPREFIX +
                    '/display/disable-checklist-descriptions', True)

    def set_desc_wait(self, spinButton, event):
        '''
        '''
        self.gconfClient.set_int(GCONFPREFIX + '/display/checklist-description-wait',
        spinButton.get_value_as_int())

    def set_gpg_path(self, fileEntry):
        '''
        '''
        self.gconfClient.set_string(GCONFPREFIX + '/files/gpg-path',
                fileEntry.gtk_entry().get_text())

    def set_gpg_identity(self, entry, event=None):
        '''
        '''
        if event:
            self.gconfClient.set_string(GCONFPREFIX + '/user/gpg-identity',
                    entry.get_text())
        else:
            self.gconfClient.set_string(GCONFPREFIX + '/user/gpg-identity',
                    entry.child.get_text())

    def set_state_dir(self, fileEntry):
        '''
        '''
        self.gconfClient.set_string(GCONFPREFIX + '/files/user-state-dir',
                fileEntry.gtk_entry().get_text())
