# File: review.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 26 March 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
"""A review object with methods to display and publish itself.
"""
__revision__ = "$Rev$"

import re, string

import gtk, gobject
import checklist

try:
    import textwrap
except ImportError:
    try:
        from optik import textwrap
    except ImportError:
        from optparse import textwrap

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

    def __init__(self, treeStore, properties):
        gobject.GObject.__init__(self)
        self.checklist = treeStore
        self.properties = properties
        self.addPaths = {}
        self.textwrap = textwrap.TextWrapper(initial_indent='* ',
                subsequent_indent='  ')

        self.set_property('homogeneous', False)
        self.resolution = gtk.Label()
        self.resolution.set_property('justify', gtk.JUSTIFY_LEFT)
        self.resolution.set_property('xalign', 0.0)
        self.__resolution_check(treeStore)
        ### FIXME: Do something about packing
        self.add(self.resolution)

        self.hashLabel = gtk.Label('MD5Sums:\n')
        self.hashLabel.set_property('justify', gtk.JUSTIFY_LEFT)
        self.hashLabel.set_property('xalign', 0.0)
        self.add(self.hashLabel)
        self.hashes = gtk.Label()
        self.hashes.set_property('justify', gtk.JUSTIFY_LEFT)
        self.hashes.set_property('xalign', 0.0)
        self.__update_hash(self.properties)
        self.add(self.hashes)

        ### FIXME: Allow editing the OUTPUT from this Widget.  Need to emit
        # row-changed signals that are picked up by the TreeStore (or else
        # change both listStore and treeStore)
        self.__generate_data(treeStore)
       
        self.goodLabel=gtk.Label('Good:')
        self.goodLabel.set_property('justify', gtk.JUSTIFY_LEFT)
        self.goodLabel.set_property('xalign', 0.0)
        self.add(self.goodLabel)
        self.goodComments = gtk.TreeView(self.list)
        self.goodComments.set_headers_visible(False)
        renderer = MyRendererText()
        column = gtk.TreeViewColumn('Output', renderer,
                                    markup=self.__OUTPUT,
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
                                    markup=self.__OUTPUT,
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
                                    markup=self.__OUTPUT,
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
                                    markup=self.__OUTPUT,
                                    resolution=self.__RESOLUTION,
                                    display=self.__DISPLAY)
        column.set_cell_data_func(renderer, self.__filter_note)
        self.noteComments.append_column(column)
        self.add(self.noteComments)

        treeStore.connect('row-changed', self.__update_data)
        treeStore.connect('row-inserted', self.__add_data)
        ### FIXME: Need to connect to a signal when the SRPM changes.
        # self.properties.connect('hash-change', self.__update_hash)

    def show(self):
        """Display the new widget"""
        self.show_all()

    def publish(self, filename):
        """Write the review to a file."""

        buffer = [self.resolution.get_text()+"\n"]
        resIter = self.list.get_iter_first()
        goodList = []
        workList = []
        minorList = []
        notesList = []
        while resIter:
            if self.list.get_value(resIter, self.__DISPLAY):
                res = self.list.get_value(resIter, self.__RESOLUTION)
                value = self.list.get_value(resIter, self.__OUTPUT)
                if value != None:
                    value = self.checklist.unpangoize_output(value)
                    value = self.textwrap.fill(value) + '\n'
                    if res == 'Pass':
                        goodList.append(value)
                    elif res == 'Fail':
                        workList.append(value)
                    elif res == 'Non-Blocker':
                        minorList.append(value)
                    elif res == 'Not-Applicable' or res == 'Needs-Reviewing':
                        notesList.append(value)
            resIter = self.list.iter_next(resIter)
            
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
        """Updates the hashes label with the current hashes in the properties"""
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

    def __update_data(self, treeStore, path, updateIter):
        """Update internal list from treeStore when treeStore is changed."""

        # row-changed gets called once for each item that is updated, even
        # when there's a group.  So we have to wait until we get a proper
        # summary (our key value) to add the entry to the list
        summary = treeStore.get_value(updateIter, checklist.SUMMARY)
        if self.addPaths.has_key(path) and summary:
            # New item
            self.list.append((summary,
                treeStore.get_value(updateIter, checklist.DISPLAY),
                treeStore.get_value(updateIter, checklist.RESOLUTION),
                treeStore.get_value(updateIter, checklist.OUTPUT)))
            del self.addPaths[path]
        elif len(path) > 1:
            # Update an old item
            listIter = self.list.get_iter_first()
            while listIter:
                if self.list.get_value(listIter, self.__SUMMARY) == summary:
                    self.list.set(listIter,
                            self.__DISPLAY,
                            treeStore.get_value(updateIter, checklist.DISPLAY),
                            self.__RESOLUTION,
                            treeStore.get_value(updateIter,
                                checklist.RESOLUTION),
                            self.__OUTPUT,
                            treeStore.get_value(updateIter, checklist.OUTPUT))
                    break
                listIter = self.list.iter_next(listIter)
        else:
            # Don't care about Categories (toplevel items)
            pass

        self.__resolution_check(treeStore)

    def __add_data(self, treeStore, path, addIter):
        """Let update know it will be handling an add soon."""

        # If it's not a Category (toplevel) row then add it to our list of
        # aditions.
        if len(path) > 1:
            self.addPaths[path] = True

    def __generate_data(self, treeStore):
        """Create the internal list from the present state of treeStore.
        
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
        category = treeStore.get_iter_first()
        while category:
            entryIter = treeStore.iter_children(category)
            while entryIter:
                self.list.append((treeStore.get_value(entryIter,
                    checklist.SUMMARY),
                    treeStore.get_value(entryIter, checklist.DISPLAY),
                    treeStore.get_value(entryIter, checklist.RESOLUTION),
                    treeStore.get_value(entryIter, checklist.OUTPUT)))
                entryIter = treeStore.iter_next(entryIter)
            category = treeStore.iter_next(category)

    def __filter_good(self, column, cell, model, entryIter):
        """Only display comments which have DISPLAY and RESOLUTION=pass."""
        
        cell.set_property('mode', gtk.CELL_RENDERER_MODE_INERT)
        if (cell.get_property('display') and 
                cell.get_property('resolution') == 'Pass'):
            cell.set_property('visible', True)
        else:
            cell.set_property('visible', False)

    def __filter_work(self, column, cell, model, entryIter):
        """Only display comments which have DISPLAY and RESOLUTION=Fail."""

        cell.set_property('mode', gtk.CELL_RENDERER_MODE_INERT)
        if (cell.get_property('display') and
                cell.get_property('resolution') == 'Fail'):
            cell.set_property('visible', True)
        else:
            cell.set_property('visible', False)
            
    def __filter_minor(self, column, cell, model, entryIter):
        """Only display comments which have DISPLAY and RESOLUTION=Minor."""

        cell.set_property('mode', gtk.CELL_RENDERER_MODE_INERT)
        if (cell.get_property('display') and
                cell.get_property('resolution') == 'Non-Blocker'):
            cell.set_property('visible', True)
        else:
            cell.set_property('visible', False)
            
    def __filter_note(self, column, cell, model, entryIter):
        """Only display comments which have DISPLAY and Not-Applicable."""

        cell.set_property('mode', gtk.CELL_RENDERER_MODE_INERT)
        if (cell.get_property('display') and
                cell.get_property('resolution') == 'Not-Applicable'):
            cell.set_property('visible', True)
        else:
            cell.set_property('visible', False)
            
    def __resolution_check(self, treeStore):
        """Checks the treeStore to decide the recommendation for this review

        This depends on the category status being correct so if there are
        bugs, be sure to check there as well.
        """
        catIter = treeStore.get_iter_first()
        moreWork = False
        while catIter:
            value = treeStore.get_value(catIter, checklist.RESOLUTION)
            if value == 'Fail':
                self.resolution.set_text('NEEDSWORK')
                return
            elif value == 'Needs-Reviewing':
                moreWork = True
             catIter = treeStore.iter_next(catIter)

        if moreWork:
            self.resolution.set_text('Incomplete Review')
        else:
            self.resolution.set_text('PUBLISH +1')

gobject.type_register(Review)
