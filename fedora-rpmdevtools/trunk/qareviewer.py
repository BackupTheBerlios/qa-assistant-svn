# File: qareviewer
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 4 Mar 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Description: Main QAReviewer application object
# Id: $Id$
"""QA Reviewer object.

The main program object.  From here we set up the user interface, receive
events, and send things off for future processing.
"""
__version__ = "0.1"
__revision__ = "$Revision$"

import libxml2
import gtk

import checklist
import gnomeglade
from optionrenderer import OptionCellRenderer

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
        column = gtk.TreeViewColumn('Display', renderer,
                                    active=checklist.DISPLAY,
                                    visible=checklist.ISITEM)
        renderer.connect('toggled', self.display_toggle)
        self.checkView.append_column(column)

        renderer = OptionCellRenderer()
        column = gtk.TreeViewColumn('pass/fail', renderer,
                                    optionlist=checklist.RESLIST,
                                    selectedoption=checklist.RESOLUTION,
                                    mode=checklist.ISITEM)
        column.set_cell_data_func(renderer, self.render_option_mode)
        renderer.connect('changed', self.resolution_changed)
        self.checkView.append_column(column)
       
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Description', renderer,
                                    text=checklist.SUMMARY)
        self.checkView.append_column(column)
        
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Output', renderer,
                                    text=checklist.OUTPUT,
                                    visible=checklist.DISPLAY)
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

    def render_option_mode(self, column, cell, model, iter):
        item = cell.get_property('mode')
        if item:
            mode=gtk.CELL_RENDERER_MODE_ACTIVATABLE
        else:
            mode=gtk.CELL_RENDERER_MODE_INERT
        cell.set_property('mode', mode)

    def resolution_changed(self, renderer, newValue, iter):
        self.checklist.tree.set(iter, checklist.RESOLUTION, newValue)
        outputlist = self.checklist.tree.get_value(iter, checklist.OUTPUTLIST)
        out = outputlist[newValue]
        self.checklist.tree.set(iter, checklist.OUTPUT, out)

        ## FIXME:
        # Check if the change makes the overall review into a pass or fail
        if newValue == 'Pass' or newValue == 'N/A' or newValue == 'Needs Reviewing':
            pass
            # Check if all the checklist items agree
        elif newValue == 'Fail':
            pass
            # One failure is enough to fail the whole section.
            # Check if the head state is already fail.  If not, change
        ### FIXME: Change the editorPane

    def display_toggle(self, cell, path, *data):
        iter = self.checklist.tree.get_iter(path)
        value = self.checklist.tree.get_value(iter, checklist.DISPLAY)
        name = self.checklist.tree.get_value(iter, checklist.SUMMARY)

        if value == True:
            self.checklist.tree.set(iter, checklist.DISPLAY, False) 
            ### FIXME: Hide the displayed output elements in the editorPane
            # Find widget by name
            # widget.destroy()
            pass
        else:
            self.checklist.tree.set(iter, checklist.DISPLAY, True)
            ### FIXME: Display the output elements in the editorPane
            # create testarea widget with name
            # fill textarea widget with checklist.OUTPUT

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

