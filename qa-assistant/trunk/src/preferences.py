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

class Preferences(gnomeglade.Component):

    def __init__(self, gladeFile):
        '''Create a new preferences dialog to take in preferences.'''
        gnomeglade.Component.__init__(self, gladeFile, 'PreferencesDialog')

        # Initialize the gconf connection
        self.gconfClient = gconf.client_get_default()

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
        disableDesc = self.gconfClient.get_bool(GCONFPREFIX +
                '/display/disable-checklist-descriptions')
        if not disableDesc:
            self.DescriptionCheckButton.set_active(True)
        self.DescriptionCheckButton.connect('toggled',
                self.set_show_description)
        key = GCONFPREFIX + '/display/checklist-description-wait'
        try:
            descWait = self.gconfClient.get_int(key)
        except gobject.GError:
            descWait = self.gconfClient.get_default_from_schema(key)
        (spinMin, spinMax) = self.DescWaitSpin.get_range()
        if descWait < spinMin or descWait > spinMax:
            descWait = self.gconfClient.get_default_from_schema(key)
        self.DescWaitSpin.set_value(descWait)
        self.DescWaitSpin.connect('focus-out-event', self.set_desc_wait)
        
        # Set Review Output and setup callback for change
        noAutoDisplay = self.gconfClient.get_bool(
                GCONFPREFIX + '/display/no-auto-display')
        if not noAutoDisplay:
            self.DisplayFailCheckButton.set_active(True)
        self.DisplayFailCheckButton.connect('toggled',
                self.set_display_on_fail)
        
        # Set the gpg options
        useGpg = self.gconfClient.get_bool(GCONFPREFIX + '/user/use-gpg')
        if useGpg:
            self.SignCheckButton.set_active(True)
        ### FIXME: Eventually we want to use Python bindings to  gpgme for this.
        gpgIdentities = gpg.list_secret_keys()

        ### self.SignIdCombo.set_items(gpgIdentities)
        gpgId = self.gconfClient.get_string(GCONFPREFIX + '/user/gpg-identity')
        if gpgId in gpgIdentities:
            ### self.SignIdCombo.set(gpgId)
            pass
        ### FIXME: Check for validity.  If valid, set.
        # Construct the list of id's from gpg output.
        # Is gpgId the gconfClient 
        # Here: line = gpg --list-secret-keys
        # os.popen('gpg --list-secret-keys')
        # In review.py:publish():
        # gpg --local-user <id> --clearsign --armor <tmpfile> > filename
        pass

        # files/user-state-dir
        # files/gpg-path
        # Connect to signals:
        # user/use-gpg
        # user/gpg-identity
        #
        # files/user-state-dir
        # 
        # If Ok button is pressed, we need to close the dialog.
        # If Help is pressed, we need to popup Not Yet Implemented.
    
    #
    # GConf setting callbacks
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

