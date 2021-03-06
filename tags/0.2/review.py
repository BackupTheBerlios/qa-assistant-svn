# File: review.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 26 March 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
"""A review object with methods to display and publish itself.
"""
__revision__ = "$Rev$"

import gtk, gobject
import checklist

class MyRendererText(gtk.CellRendererText):
    __gproperties__ = {
        'resolution' : (gobject.TYPE_STRING, 'Resolution state',
        'how the reviewer resolves this checklist item',
        '', gobject.PARAM_READWRITE),
        'display' : (gobject.TYPE_BOOLEAN, 'Display state',
        'is this item selected for display in the review?',
        False, gobject.PARAM_READWRITE),
    }
    def __init__(self):
        self.__gobject_init__()
        setattr(self, 'display', False)
        setattr(self, 'resolution', '')

    def do_set_property(self, id, value):
        if not hasattr(self, id.name):
            raise AttributeError, 'unknown property %s' % (id.name)
        setattr(self, id.name, value)

    def do_get_property(self, id):
        return getattr(self, id.name)

gobject.type_register(MyRendererText)

class Review(gtk.VBox):
    __SUMMARY=0
    __DISPLAY=1
    __RESOLUTION=2
    __OUTPUT=3

    def __init__(self, tree, properties):
        gobject.GObject.__init__(self)
        self.tree = tree
        self.properties = properties

        self.set_property('homogeneous', False)
        self.resolution = gtk.Label()
        self.resolution.set_property('justify', gtk.JUSTIFY_LEFT)
        self.resolution.set_property('xalign', 0.0)
        self.__resolution_check()
        ### FIXME: Do something about packing
        self.add(self.resolution)

        self.hashLabel = gtk.Label('MD5Sums:\n')
        self.hashLabel.set_property('justify', gtk.JUSTIFY_LEFT)
        self.hashLabel.set_property('xalign', 0.0)
        self.add(self.hashLabel)
        self.hashes = gtk.Label()
        self.__update_hash(self.properties)
        self.add(self.hashes)

        ### FIXME: Allow editing the OUTPUT from this Widget.  Need to emit
        # row-changed signals that are picked up by the TreeStore (or else
        # change both listStore and treeStore)
        self.__generate_data()
       
        self.goodLabel=gtk.Label('Good:')
        self.goodLabel.set_property('justify', gtk.JUSTIFY_LEFT)
        self.goodLabel.set_property('xalign', 0.0)
        self.add(self.goodLabel)
        self.goodComments = gtk.TreeView(self.list)
        self.goodComments.set_headers_visible(False)
        renderer = MyRendererText()
        column = gtk.TreeViewColumn('Output', renderer,
                                    text=self.__OUTPUT,
                                    resolution=self.__RESOLUTION,
                                    display=self.__DISPLAY)
        column.set_cell_data_func(renderer, self.__filter_good)
        self.goodComments.append_column(column)
        self.add(self.goodComments)

        self.workLabel=gtk.Label('Needswork:')
        self.workLabel.set_property('justify', gtk.JUSTIFY_LEFT)
        self.workLabel.set_property('xalign', 0.0)
        self.add(self.workLabel)
        self.workComments = gtk.TreeView(self.list)
        self.workComments.set_headers_visible(False)
        renderer = MyRendererText()
        column = gtk.TreeViewColumn('Output', renderer,
                                    text=self.__OUTPUT,
                                    resolution=self.__RESOLUTION,
                                    display=self.__DISPLAY)
        column.set_cell_data_func(renderer, self.__filter_work)
        self.workComments.append_column(column)
        self.add(self.workComments)
        
        self.minorLabel=gtk.Label('Minor:')
        self.minorLabel.set_property('xalign', 0.0)
        self.minorLabel.set_property('justify', gtk.JUSTIFY_LEFT)
        self.add(self.minorLabel)
        self.minorComments = gtk.TreeView(self.list)
        self.minorComments.set_headers_visible(False)
        renderer = MyRendererText()
        column = gtk.TreeViewColumn('Output', renderer,
                                    text=self.__OUTPUT,
                                    resolution=self.__RESOLUTION,
                                    display=self.__DISPLAY)
        column.set_cell_data_func(renderer, self.__filter_minor)
        self.minorComments.append_column(column)
        self.add(self.minorComments)
        
        self.noteLabel=gtk.Label('Notes:')
        self.noteLabel.set_property('xalign', 0.0)
        self.noteLabel.set_property('justify', gtk.JUSTIFY_LEFT)
        self.add(self.noteLabel)
        self.noteComments = gtk.TreeView(self.list)
        self.noteComments.set_headers_visible(False)
        renderer = MyRendererText()
        column = gtk.TreeViewColumn('Output', renderer,
                                    text=self.__OUTPUT,
                                    resolution=self.__RESOLUTION,
                                    display=self.__DISPLAY)
        column.set_cell_data_func(renderer, self.__filter_note)
        self.noteComments.append_column(column)
        self.add(self.noteComments)

        self.tree.connect('row-changed', self.__update_data)
        ### FIXME: Need to connect to a signal when the SRPM changes.
        # self.properties.connect('hash-change', self.__update_hash)

    def show(self):
        """Display the new widget"""
        self.show_all()

    def publish(self, filename):
        """Write the review to a file."""

        buffer = [self.resolution.get_text()+"\n"]
        iter = self.list.get_iter_first()
        goodList = []
        workList = []
        minorList = []
        notesList = []
        while iter:
            if self.list.get_value(iter, self.__DISPLAY) == True:
                res = self.list.get_value(iter, self.__RESOLUTION)
                value = self.list.get_value(iter, self.__OUTPUT)
                if value != None:
                    if res == 'Pass':
                        goodList.append('* ' + value + "\n")
                    elif res == 'Fail':
                        workList.append('* ' + value + "\n")
                    elif res == 'Non-Blocker':
                        minorList.append('* ' + value + "\n")
                    elif res == 'Not-Applicable' or res == 'Needs-Reviewing':
                        notesList.append('* ' + value + "\n")
            iter = self.list.iter_next(iter)
            
        buffer+=("\n", "MD5Sums:\n", self.hashes.get_text())
        if len(goodList) > 0:
            buffer+=["\n", "Good:\n"] + goodList
        if len(workList) > 0:
            buffer+=["\n", "Needswork:\n"] + workList
        if len(minorList) > 0:
            buffer+=["\n", "Minor:\n"] + minorList
        if len(notesList) > 0:
            buffer+=["\n", "Notes:\n"] + notesList

        outfile = file(filename, 'w')
        outfile.writelines(buffer)
        outfile.close()

    def submit(self):
        pass

    def update_hash(self):
        """See __update_hash"""
        ### FIXME: This is a stopgap until we make properties a gobject and can
        # connect to a signal for SRPM changes there.
        self.__update_hash(self.properties)

    def __update_hash(self, properties):
        """Updates the hashes label withthe current hashes in the properties"""
        if self.properties.SRPM:
            srpmhash, sourcehashes = self.properties.SRPM.hashes()
            (file, hash) = srpmhash.popitem()
            hashBuf = hash + '  ' + file + "\n"
            while sourcehashes:
                (file, hash) = sourcehashes.popitem()
                hashBuf += hash + '  ' + file + "\n"
        else:
            hashBuf = ""
        self.hashes.set_text(hashBuf)

    def __update_data(self, treeStore, path, iter):
        """Update internal list from changes to treeStore on row-changed."""

        name = self.tree.get_value(iter, checklist.SUMMARY)
        listIter = self.list.get_iter_first()
        while listIter:
            if self.list.get_value(listIter, self.__SUMMARY) == name:
                self.list.set(listIter,
                  self.__DISPLAY, treeStore.get_value(iter, checklist.DISPLAY),
                  self.__RESOLUTION,
                  treeStore.get_value(iter, checklist.RESOLUTION),
                  self.__OUTPUT, treeStore.get_value(iter, checklist.OUTPUT))
                break
            listIter = self.list.iter_next(listIter)

        self.__resolution_check()

    def __generate_data(self):
        """Create the internal list from the present state of tree.
        
        Take data from the TreeModel and put it into a ListStore.  We only
        need DISPLAY and RESOLUTION to decide how the data is too be displayed
        and OUTPUT as the actual data we will show.  We do not display
        categories, only entries.

        __update_data is used to keep the ListStore synced with the TreeStore
        whenever the TreeStore emits row-changed.
        """
        
        self.list = gtk.ListStore(gobject.TYPE_STRING,
                                  gobject.TYPE_BOOLEAN,
                                  gobject.TYPE_STRING,
                                  gobject.TYPE_STRING)
        category = self.tree.get_iter_first()
        while category:
            iter = self.tree.iter_children(category)
            while iter:
                self.list.append((self.tree.get_value(iter, checklist.SUMMARY),
                              self.tree.get_value(iter, checklist.DISPLAY),
                              self.tree.get_value(iter, checklist.RESOLUTION),
                              self.tree.get_value(iter, checklist.OUTPUT)))
                iter = self.tree.iter_next(iter)
            category = self.tree.iter_next(category)

    def __filter_good(self, column, cell, model, iter):
        """Only display comments which have DISPLAY and RESOLUTION=pass."""
        
        cell.set_property('mode', gtk.CELL_RENDERER_MODE_INERT)
        if (cell.get_property('display') and 
                cell.get_property('resolution') == 'Pass'):
            cell.set_property('visible', True)
        else:
            cell.set_property('visible', False)

    def __filter_work(self, column, cell, model, iter):
        """Only display comments which have DISPLAY and RESOLUTION=Fail."""

        cell.set_property('mode', gtk.CELL_RENDERER_MODE_INERT)
        if (cell.get_property('display') and
                cell.get_property('resolution') == 'Fail'):
            cell.set_property('visible', True)
        else:
            cell.set_property('visible', False)
            
    def __filter_minor(self, column, cell, model, iter):
        """Only display comments which have DISPLAY and RESOLUTION=Minor."""

        cell.set_property('mode', gtk.CELL_RENDERER_MODE_INERT)
        if (cell.get_property('display') and
                cell.get_property('resolution') == 'Non-Blocker'):
            cell.set_property('visible', True)
        else:
            cell.set_property('visible', False)
            
    def __filter_note(self, column, cell, model, iter):
        """Only display comments which have DISPLAY and Not-Applicable."""

        cell.set_property('mode', gtk.CELL_RENDERER_MODE_INERT)
        if (cell.get_property('display') and
                cell.get_property('resolution') == 'Not-Applicable'):
            cell.set_property('visible', True)
        else:
            cell.set_property('visible', False)
            
    def __resolution_check(self):
        """Checks the treeStore to decide the recommendation for this review

        This depends on the category status being correct so if there are
        bugs, be sure to check there as well.
        """
        iter = self.tree.get_iter_first()
        moreWork = False
        while iter:
            value = self.tree.get_value(iter, checklist.RESOLUTION)
            if value == 'Fail':
                self.resolution.set_text('NEEDSWORK')
                return
            elif value == 'Needs-Reviewing':
                moreWork = True
            iter = self.tree.iter_next(iter)

        if moreWork:
            self.resolution.set_text('Incomplete Review')
        else:
            self.resolution.set_text('PUBLISH +1')

gobject.type_register(Review)
