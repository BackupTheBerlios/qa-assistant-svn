# File: qareviewer
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 4 Mar 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Description: Main QAReviewer application object
# Id: $Id$
"""
"""
__version__ = "0.1"
__revision__ = "$Revision$"

import libxml2
import gtk

import checklist
import gnomeglade

class CellRendererEnum(gtk.CellRenderer):
    """ Renders a multi-state as a combo box. """ 

class QAReviewer(gnomeglade.GnomeApp):
    def __init__(self, arguments):
        """Creates a new QA reviewer window.
           
        Keyword -- arguments:
        arguments: A commandline to process when setting up the environment
        """
       
        gladefile = 'glade/fedora-qareviewer.glade'
        gnomeglade.GnomeApp.__init__(self, __name__, __version__, gladefile,
                'ReviewerWindow')
        # load the checklist data
        try:
            self.checklist = checklist.CheckList('data/fedoraus.xml')
        except (libxml2.parserError, checklist.Error), msg:
            sys.stderr.write("Unable to parse the checklist: %s\n" % (msg))
            sys.exit(1)

        # Create a treeview for our listPane
        self.checkView = gtk.TreeView(self.checklist.tree)
        self.checkView.set_rules_hint(True)
        ### FIXME: Other optional methods of TreeView configuration here.
        
        renderer = gtk.CellRendererToggle()
        renderer.set_radio(False)
        column = gtk.TreeViewColumn('Display', renderer, active=checklist.DISPLAY)
        column.set_clickable(True)
        self.checkView.append_column(column)

        ### FIXME: Add a renderer for enumerations as passed via RESOLUTION
        # We can render toggles with multiple buttons depending on the
        # resolution
        # renderer = CellRendererEnum()
        # column = gtk.TreeViewColumn('pass/fail', renderer, initial=RESOLUTION)
        # column.set_?clickable?(True)
        # checkView.append_column(column)
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('pass/fail', renderer, text=checklist.RESOLUTION)
        column.set_clickable(True)
        self.checkView.append_column(column)
        
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Description', renderer, text=checklist.SUMMARY)
        self.checkView.append_column(column)
        
        column = gtk.TreeViewColumn('Output', renderer, text=checklist.OUTPUT)
        self.outputColumn = column
        self.checkView.append_column(column)

        self.listPane.add(self.checkView)

        self.grabArrow=gtk.Arrow(gtk.ARROW_LEFT, gtk.SHADOW_NONE)
        self.grabArrow.set_size_request(4,4)
        label=self.grabBar.get_child()
        self.grabBar.remove(label)
        self.grabBar.add(self.grabArrow)

        # Hide the editorPane until the user asks to see it.
        self.mainDisplay.remove(self.editorPane)

        self.ReviewerWindow.show_all()

        ### FIXME
        # Use gtk.OptionMenu instead of gtk.ComboBox as glade2 defines

    def on_menu_quit_activate(self, *extra):
        """Delete a window.

        Callback to delete a window.
        """

        ### FIXME:
        # Check for unsaved files.
        self.quit()
       
    def on_menu_about_activate(self, *extra):
        """Show the about window."""

        about = gtk.glade.XML('glade/fedora-qareviewer.glade', 'AboutWindow').get_widget('AboutWindow')
        about.set_property('name', __programName__)
        about.set_property('version', __version__)
        about.show()

    def on_grabBar_clicked(self, *extra):
        """Mimic a moving shade that displays an alternate view of the review.

        """

        if self.grabArrow.get_property('arrow-type') == gtk.ARROW_LEFT:
            self.grabArrow.set(gtk.ARROW_RIGHT, gtk.SHADOW_NONE)
            self.checkView.remove_column(self.outputColumn)
            self.mainDisplay.pack_end(self.editorPane)
        else:
            self.grabArrow.set(gtk.ARROW_LEFT, gtk.SHADOW_NONE)
            self.checkView.append_column(self.outputColumn)
            self.mainDisplay.remove(self.editorPane)

    def on_delete_event(self, *extra):
        """Delete a window.
        
        Callback to delete a window.
        """

        return self.on_menu_quit_activate()

