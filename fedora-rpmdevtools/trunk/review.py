# File: review.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 26 March 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
"""A review object with methods to display and publish itself.
"""
__revision__ = "$Revision$"

import gtk

class Review(gtk.VBox):
    
    def __init__(self, tree, properties):
        self.vbox = gtk.VBox()
        self.resolution = gtk.ComboBox()
        self.goodComments = gtk.ListView()
        self.needsworkComments = gtk.ListView()
        self.minorComments = gtk.ListView()
        self.md5sums = gtk.Label()
        self.vbox.add(self.resolution)
        # VBox 1: Resolution state
        # VBox 2: Label Good:
        # VBox 3: ListView Good:
        # VBox 4: Label Needswork
        # VBox 5: Listview Needswork
        # VBox 6: Label Minor
        # VBox 7: Listview Minor
        # VBox 8: MDSums (Non editable textview)
        # Set up the association between the tree and the Review widget.
        pass

    def show(self):
        # Display the new widget.
        self.vbox.show_all()
        pass

    def publish(self):
        pass

    def submit(self):
        pass
