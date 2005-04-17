# File: propview.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 17 February 2005
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
'''UI to allow properties to be entered into the checklist.'''
__revision__ = "$Rev$"

import gtk

import properties

class PropertiesView(gtk.HBox):
    '''View and set Properties on a CheckList.

    PropertiesView displays and sets properties on the model.
    '''
    # What things are we going to do to the model?
    # We need to create a widget that allows setting of the properties.
    #  - The widget must have a callback that checks if it has all required
    #    entries.
    #  - Automatic properties must be notified when their dependents are
    #    modified so they can auto update.
    #
    def __init__(self, model=None):
        gtk.HBox.__init__(self)
        self.set_spacing(7)

        self.model = model
        self.create_layout()
            
    def create_layout(self):
        '''
        '''
        props = self.model
        if not props:
            label = gtk.Label('This CheckList does not contain any properties.')
            self.add(label)
            label.show()
            return
        
        self.labels = gtk.VBox()
        self.entries = gtk.VBox()
        self.add(self.labels)
        self.add(self.entries)
        self.propDisplays = {}

        for propName in props.keys():
            label = gtk.Label(propName)
            self.labels.add(label)
            label.show()
            if props[propName].propType == 'automatic':
                value = props[propName].value or '<No value>'
                self.propDisplays[propName] = gtk.Label(value)
            else:
                value = props[propName].value or ''
                entry = gtk.Entry()
                entry.set_text(value)
                entry.connect('focus-out-event', self._change_property,
                        propName)
                self.propDisplays[propName] = entry
            self.propDisplays[propName].show()
            self.entries.add(self.propDisplays[propName])

        self.labels.show()
        self.entries.show()
            
    def _change_property(self, entry, event, propName):
        '''Set the property in the model from the entry.

        Changing the value in the entry needs to be reflected in the
        Properties model.  This callback sets that value whenever focus
        leaves an entry.
        '''
        self.model[propName] = entry.get_text()
        
    def set_model(self, model):
        '''Change the Properties that this PropWidget is displaying,

        Arguments:
        :model: Properties object that the widget is displaying.

        '''
        self.model = model
        self.foreach(self.remove)
        self.create_layout()

class PropertiesDialog(gtk.Window):
    '''Class to wrap a properties widget inside a window.'''

    def __init__(self, prop=None):
        '''
        '''
        # Initialize the parent dialog
        gtk.Window.__init__(self)
        self.set_border_width(5)
        self.set_title('Set Checklist Properties')

        # Layout items in a VBox.
        self.vbox = gtk.VBox()
        self.vbox.set_spacing(5)
        self.add(self.vbox)
        # Create a widget to display the properties.
        self.propView = PropertiesView(prop)
        self.vbox.add(self.propView)

        # Create a separator
        self.separator = gtk.HSeparator()
        self.vbox.add(self.separator)

        # Add the buttons in an action area
        self.action_area = gtk.HButtonBox()
        self.vbox.add(self.action_area)
        self.help_button = gtk.Button(gtk.STOCK_HELP)
        self.help_button.set_use_stock(True)
        self.ok_button = gtk.Button(gtk.STOCK_OK)
        self.ok_button.set_use_stock(True)
        self.action_area.pack_start(self.help_button)
        self.action_area.pack_end(self.ok_button)
        self.ok_button.connect('clicked', self._ok_button_cb)
        self.help_button.connect('clicked', self._help_button_cb)

        self.ok_button.show()
        self.help_button.show()
        self.action_area.show()
        self.separator.show()
        self.propView.show()
        self.vbox.show()
        
    def set_model(self, prop):
        '''Change the Properties model that we are using.
        '''
        self.propView.set_model = prop

    def _ok_button_cb(self, *extra):
        '''Close the properties window.
        '''
        self.destroy()

    def _help_button_cb(self, *extra):
        '''Open a help window.
        '''
        pass
