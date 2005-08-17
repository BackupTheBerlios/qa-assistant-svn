# File: ui.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 6 July 2005
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
'''
'''
__revision__ = '$Rev$'

import gtk

class UI(gtk.UIManager):
    def __init__(self, app):
        '''Create the specific uiManager for this program.
        '''
        # Menu and toolbar definition
        uiElements = '''<ui>
          <menubar name="MainMenu">
            <menu action="File">
              <menuitem action="New"/>
              <menuitem action="Open"/>
              <menuitem action="Save"/>
              <menuitem action="Save As"/>
              <separator/>
              <menuitem action="Quit"/>
            </menu>
            <menu action="Edit">
              <menuitem action="Cut"/>
              <menuitem action="Copy"/>
              <menuitem action="Paste"/>
              <separator/>
              <menuitem action="Properties"/>
              <separator/>
              <menuitem action="Preferences"/>
              <placeholder />
            </menu>
            <menu action="QAActions"/>
            <menu action="View">
              <menuitem action="Toggle Preview"/>
              <placeholder />
            </menu>
            <menu action="Help">
              <menuitem action="Contents"/>
              <placeholder name="CheckListSpecificHelp"/>
              <menuitem action="About"/>
            </menu>
          </menubar>
          <toolbar name="MainToolBar">
            <toolitem action="New"/>
            <toolitem action="Open"/>
            <toolitem action="Save"/>
            <separator/>
          </toolbar>
        </ui>
        '''

        gtk.UIManager.__init__(self)
        self._create_action_groups(app)
        for group in self.groups.values():
            self.insert_action_group(group, pos=0)
        self.add_ui_from_string(uiElements)
        del uiElements

    def _create_action_groups(self, app):
        ''' Initializes the actiongroups.
        '''
        self.groups = {}

        # Base actiongroup is always available.  It holds items the program
        # can perform whether or not any checklist is loaded.
        self.groups['base'] = gtk.ActionGroup('base')
        actions = (
            ('File', None, '_File'),
            ('Edit', None, '_Edit'),
            ('View', None, '_View'),
            ('Help', None, '_Help'),
            ('New', gtk.STOCK_NEW, None, None,
                'Start filling in a fresh checklist', app.new_cb),
            ('Open', gtk.STOCK_OPEN, None, None,
                'Open a checklist already begun to fill out', app.open_cb),
            ('Quit', gtk.STOCK_QUIT, None, None,
                'Quit the program', app.quit_cb),
            ('Preferences', gtk.STOCK_PREFERENCES, None, None,
                'Configure the program', app.preferences_cb),
            ('Contents', gtk.STOCK_HELP, None, None,
                'Help on using QA Assisstant', app.help_cb),
            ('About', gtk.STOCK_ABOUT, None, None,
                'About QA Assistant', app.about_cb))
        self.groups['base'].add_actions(actions, app)

        # checklist actiongroup is activated whenever a checklist is present.
        self.groups['checklist'] = gtk.ActionGroup('checklist')
        actions = (('QAActions', None, '_QA Actions'),
                ('Cut', gtk.STOCK_CUT, None, None,
            'Cut the highlighted text', app.cut_cb),
            ('Copy', gtk.STOCK_COPY, None, None,
                'Copy the highlighted text to the clipboard', app.copy_cb),
            ('Paste', gtk.STOCK_PASTE, None, None,
                'Paste the clipboard into the application', app.paste_cb),
            ('Properties', gtk.STOCK_PROPERTIES, None, None,
                'Set the checklist\'s properties', app.properties_cb))
        self.groups['checklist'].add_actions(actions, app)
        self.groups['checklist'].add_toggle_actions((('Toggle Preview', None,
            '_Toggle Preview', '<control>t',
            'Toggle showing the Review preview',
            app.toggle_preview_cb, False),), app)
        self.groups['checklist'].set_sensitive(False)
        
        # Menu items active whenever a checklist is modified
        self.groups['modified'] = gtk.ActionGroup('modified')
        actions = (('Save', gtk.STOCK_SAVE, None, None,
            'Save the checklist', app.save_cb),
            ('Save As', gtk.STOCK_SAVE_AS, None, None,
                'Save the checklist to a different file', app.save_as_cb))
        self.groups['modified'].add_actions(actions, app)
        self.groups['modified'].set_sensitive(False)
