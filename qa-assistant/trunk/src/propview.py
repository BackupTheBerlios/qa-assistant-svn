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

        self.model = model
        self.create_layout()
            
    def create_layout(self):
        '''
        '''
        props = self.model
        if not props:
            self.add(gtk.Label(
                'This Checklist does not contain any properties.'))
            return
        
        self.labels = gtk.VBox()
        self.entries = gtk.VBox()
        self.add(self.labels)
        self.add(self.entries)
        self.propDisplays = {}

        for propName in props.keys():
            label = gtk.Label(propName)
            self.labels.add(label)
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
            self.entries.add(self.propDisplays[propName])
            
    def _change_property(self, entry, event, propName):
        '''

        '''
        self.model[propName] = entry.get_text()
        
    ### FIXME: Method to tell us if all onload Properties have been satisfied

    def set_model(self, model):
        '''Change the Properties that this PropWidget is displaying,

        Arguments:
        :model: Properties object that the widget is displaying.

        '''
        self.model = model
        self.foreach(self.remove)
        self.create_layout()
