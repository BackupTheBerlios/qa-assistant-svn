# File: checkview.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 10 September, 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
''' Viewer for the CheckList class.
'''
__revision__ = '$Rev$'

import gtk
import gconf

from qaconst import *
from optionrenderer import OptionCellRenderer
from treetips import TreeTips
import checklist

class CheckView(gtk.TreeView):
    def __init__(self, checkList=None):
        gtk.TreeView.__init__(self, checkList)
        self.set_rules_hint(True)

        renderer = gtk.CellRendererToggle()
        renderer.set_radio(False)
        column = gtk.TreeViewColumn('Display', renderer,
                                    active=checklist.DISPLAY,
                                    visible=checklist.ISITEM)
        renderer.connect('toggled', self.display_toggle)
        self.append_column(column)

        renderer = OptionCellRenderer()
        column = gtk.TreeViewColumn('Resolution', renderer,
                                    optionlist=checklist.RESLIST,
                                    selectedoption=checklist.RESOLUTION,
                                    mode=checklist.ISITEM)
        column.set_cell_data_func(renderer, self.__translate_option_mode)
        renderer.connect('changed', self.resolution_changed)
        self.append_column(column)
       
        renderer = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Summary', renderer,
                                    text=checklist.SUMMARY)
        self.append_column(column)
        
        renderer = gtk.CellRendererText()
        renderer.connect('edited', self.output_edited)
        column = gtk.TreeViewColumn('Output', renderer,
                                    markup=checklist.OUTPUT,
                                    visible=checklist.DISPLAY,
                                    editable=checklist.DISPLAY)
        self.outputColumn = column
        self.outputHidden = False
        self.append_column(column)

        self.tips = TreeTips(self, checklist.DESC)

        # Get preferences from gconf for setting the treetip help.
        self.gconfClient = gconf.client_get_default()
        self.gconfClient.add_dir(GCONFPREFIX, gconf.CLIENT_PRELOAD_NONE)
        key = GCONFPREFIX + '/disable-checklist-descriptions'
        self.gconfClient.notify_add(key, self.__change_treetip_show)
        if self.gconfClient.get_bool(key):
            self.tips.disable()
        else:
            self.tips.enable()
        key = GCONFPREFIX + '/checklist-description-wait'
        self.gconfClient.notify_add(key, self.__change_treetip_delay)
        tipDelay = self.gconfClient.get_int(key)
        if tipDelay:
            self.tips.set_property('delay', tipDelay)

    def display_output(self, display):
        '''Hides or shows the output column.

        Arguments:
        display -- Boolean deciding whether we want to show the column.
        '''
        if display and self.outputHidden:
            self.append_column(self.outputColumn)
            self.outputHidden = False
        else:
            self.outputHidden or self.remove_column(self.outputColumn)
            self.outputHidden = True

    def resolution_changed(self, renderer, newValue, changedRow):
        '''Changes the display when the user changes an item's state.

        Arguments:
        renderer -- renderer object emitting the signal
        newValue -- resolution type we're changing to
        changedRow -- iter pointing to the node in the tree we're operating on
    
        This method is designed to be used as a signal handler when the
        resolution changes on a treeView.  It is a bit of a hack as it calls
        a method on the checklist when the checklist should really connect
        via a signal.  The reason we don't do that is the signal connection
        would force the checklist to be defined before the checkView.  This
        is unnecessary.  Thus this callback.
        '''

        # Set the checklist to the new resolution and output values
        self.get_model().set(changedRow, checklist.RESOLUTION, newValue)
       
    def display_toggle(self, cell, path, *data):
        '''Toggles outputting a message for the review.

        Arguments:
        cell -- displayed cell we were called on
        path -- path to the cell
        data -- additional user data.  None for now.

        The display toggle allows the user to choose whether to write a
        message about the Pass or Failure state of the reviewed item.  This
        callback takes care of setting the state in the TreeStore.
        ''' 
        checkModel = self.get_model()
        entryIter = checkModel.get_iter(path)
        value = checkModel.get_value(entryIter, checklist.DISPLAY)

        if value:
            checkModel.set(entryIter, checklist.DISPLAY, False)
        else:
            checkModel.set(entryIter, checklist.DISPLAY, True)
            
    def output_edited(self, cell, row, newValue):
        '''Change the text of the output string in the checklist.
        
        Arguments:
        cell -- cell that was changed.
        row -- stringified path pointing to the changed row.
        newValue -- newValue entered into the row's output column.

        Callback to handle changes to the row's output string.  We update
        the row in the checklist to have the new value.
        '''
        checkModel = self.get_model()
        rowIter = checkModel.get_iter_from_string(row)
        res = checkModel.get_value(rowIter, checklist.RESOLUTION)
        outDict = checkModel.get_value(rowIter, checklist.OUTPUTLIST)
        outDict[res] = newValue

        checkModel.set(rowIter, checklist.OUTPUT, newValue)

        ### FIXME: Is the following necessary?
        path = checkModel.get_path(rowIter)
        checkModel.row_changed(path, rowIter)

    def __translate_option_mode(self, column, cell, model, rowIter):
        '''Translate from header/item value to mode type.

        Arguments:
        column -- column we're rendering
        cell -- cell to perform our transformation on
        model -- tree model our data lives in
        rowIter -- reference to the cell we're operating on

        The mode of the cell depends on whether it is a header/category or an
        item/entry.  However, that is a boolean value and the mode needs to
        be of mode type.  So this function selects the proper mode type
        depending on whether we're rendering a header or an entry.
        '''
        item = cell.get_property('mode')
        if item:
            mode=gtk.CELL_RENDERER_MODE_ACTIVATABLE
        else:
            mode=gtk.CELL_RENDERER_MODE_INERT
        cell.set_property('mode', mode)

        #
        # GConf helper functions
        #
        
    def __change_treetip_show(self, client, connectID, entry, extra):
        '''Enable and disable showing the help description.

        '''
        if entry.value and entry.value.type == gconf.VALUE_BOOL:
            if entry.value.get_bool():
                self.tips.disable()
            else:
                self.tips.enable()

    def __change_treetip_delay(self, client, connectID, entry, extra):
        '''Change the timeout before the help is displayed.

        '''
        if entry.value and entry.value.type == gconf.VALUE_INT:
            delay = entry.value.get_int()
            if delay:
                self.tips.set_property('delay', delay)
            else:
                self.tips.set_property('delay', 500)

