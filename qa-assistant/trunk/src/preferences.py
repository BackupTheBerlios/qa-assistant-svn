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
import re

import gtk
import gconf
import gobject

import gnomeglade
from qaconst import *

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

        # files/gpg-path
        key = GCONFPREFIX + '/files/gpg-path'
        try:
            gpgPath = self.gconfClient.get_string(key)
        except gobject.GError:
            gpgPath = self.gconfClient.get_default_from_schema(key).get_string()
        self.GPGPathEntry.set_filename(gpgPath)
        self.GPGPathEntry.connect('changed', self.set_gpg_path)
        self.gconfClient.notify_add(key, self.change_gpg_path)

        self.create_gpg_ids_list(gpgPath)
        self.SignIdCombo.connect('changed', self.set_gpg_identity)
        
        key = GCONFPREFIX + '/files/user-state-dir'
        try:
            stateDir = self.gconfClient.get_string(key)
        except gobject.GError:
            stateDir = (
                    self.gconfClient.get_default_from_schema(key).get_string())
        self.StateDirEntry.set_filename(stateDir)
        self.StateDirEntry.connect('changed', self.set_state_dir)

        ### FIXME:
        # If Ok button is pressed, we need to close the dialog.
        # If Help is pressed, we need to popup Not Yet Implemented.
        
    #
    # Functions to create the dialog
    #
        
    def create_gpg_ids_list(self, gpgPath):
        '''
        '''
        key = GCONFPREFIX + '/user/gpg-identity'
        model = self.SignIdCombo.get_model()
        try:
            gpgId = self.gconfClient.get_string(key)
        except gobject.GError:
            gpgId = None
        gpgIdentities = gpg.list_secret_keys(gpgPath)
        if gpgId:
            model.append((gpgId,))
            self.SignIdCombo.set_active(0)
            idRE = re.compile(gpgId)
            for identity in gpgIdentities:
                if idRE.match(identity):
                    continue
                model.append((identity,))
        else:
            for identity in gpgIdentities:
                model.append((identity,))

    #
    # Notify callbacks to change the GUI state
    #
    
    def change_gpg_path(self, client, connectId, entry, extra):
        '''Update the gpgID list when the gpg program is updated.
        '''
        if entry.value and entry.value.type == gconf.VALUE_STRING:
            create_gpg_ids_list(entry.value.get_string())
        
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

    def set_gpg_path(self, comboBox):
        '''
        '''
        model = comboBox.get_model()
        self.gconfClient.set_string(GCONFPREFIX + '/files/gpg-path',
                model.get_value(comboBox.get_active_iter(),0))

    def set_gpg_identity(self, comboBox):
        '''
        '''
        model = comboBox.get_model()
        self.gconfClient.set_string(GCONFPREFIX + '/user/gpg-identity',
                model.get_value(comboBox.get_active_iter(),0))

    def set_state_dir(self, comboBox):
        '''
        '''
        model = comboBox.get_model()
        self.gconfClient.set_string(GCONFPREFIX + '/files/user-state-dir',
                model.get_value(comboBox.get_active_iter(),0))
