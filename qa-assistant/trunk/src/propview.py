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
    '''

    '''
    # The Properties structure holds information about all the properties on
    # the checklist.  We are going to use this as the model.
    #
    # What things are we going to do to the model?
    # We need to create a widget that allows setting of the properties.
    #  - The widget must have a callback that checks if it has all required
    #    entries.
    #  - Automatic properties must be notified when their dependents are
    #    modified so they can auto update.
    #
    def __init__(self, model=None):
        gtk.HBox.__init__(self)

        self.model = model
        if model:
            self.create_layout()
            
    def create_layout(self):
        '''
        '''
        props = self.model
        
        self.labels = gtk.VBox()
        self.entries = gtk.VBox()
        self.add(self.labels)
        self.add(self.entries)
        self.propDisplays = {}

        for propName in props.keys():
            label = gtk.Label(propName)
            self.labels.add(label)
            value = props[propName].value or ''
            if props[propName].propType == 'automatic':
                self.propDisplays[propName] = gtk.Label(value)
            else:
                self.propDisplays[propName] = gtk.Entry()
                self.propDisplays[propName].set_text(value)
                ### FIXME: Set a callback to update properties when Entry
                # changes are "committed"
            self.entries.add(self.propDisplays[propName])
            
    ### FIXME: Method to tell us if all onload Properties have been satisfied

    def set_model(self, model):
        '''Change the Properties that this PropWidget is displaying,

        Arguments:
        :model: Properties object that the widget is displaying.

        '''
        self.model = model
        self.foreach(self.remove)
        self.create_layout()
