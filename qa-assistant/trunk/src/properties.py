# File: properties.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 22 January 2005
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
'''A class that holds properties on a review file.'''
__revision__ = "$Rev$"

import gtk

class Properties:
    def __init__(self):
        pass
class PropertiesWidget(gtk.Table):
    '''

    '''
    # The checklist holds information about the properties.
    # So this is a view of that model.
    #
    # What things are we going to do to the model?
    # We need to create a widget that allows setting of the properties.
    #  - The widget must have a callback that checks if it has all required
    #    entries.
    #  - Automatic properties must be notified when their dependents are
    #    modified so they can auto update.
    #
    # We need to export the properties to the review somehow.... This could be
    # done via the checklist....
    #
    # Functions are invoked somehow that take the properties information and
    # saves it as a 
    #
    # Have checks that verify that a given type fulfills the requirements (of
    # int, URL, etc)
    #
    def __init__(self, checklist=None):
        gtk.Table.__init__(self, columns=2)
        self.model = checklist
        if checklist:
            self.create_layout()
            
    def create_layout(self):
        props = self.model.properties
        numProps = len (props)
        # Resize for the right number of widgets
        self.resize(numProps, 2)
        
        # We need to order the properties before doing this.
        # Type: onLoad
        # Type: onPublish
        # Type: optional
        # Type: automatic
        # Or we might want to have things ordered according to what values
        # they depend on.  So primarily x depends on y.  Secondarily type
        # info.
        for i in numProps:
            label = gtk.Label()
            self.entries.append(gtk.Entry())
            self.place(label)
            
        # Place property labels in one column
        # Place entry boxes in the other
        # At the bottom, place two labels, for each auto determined property.

    def set_model(checklist):
        self.model = checklist
        if self.layout:
            self.layut.destory()
        self.create_layout()
