# File: optionrenderer.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 10 Mar 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Description:
# Id: $Id$
"""Cell Renderer to display a list of options that the user may select from.
"""
__revision__ = "$Rev$"

import gtk
import gobject

class OptionCellRenderer(gtk.GenericCellRenderer):
    __gproperties__ = {
        'optionlist' : (gobject.TYPE_PYOBJECT, 'optionList', 'list of options to render', gobject.PARAM_READWRITE),
        'selectedoption' : (gobject.TYPE_STRING, 'option', 'currently selected option', '', gobject.PARAM_READWRITE),
    }
    propertyNames = __gproperties__.keys()
    __gsignals__ = {
        'clicked' : (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        'changed' : (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_PYOBJECT))
    }
    
    def __init__(self):
        self.__gobject_init__()
        self.xpad=2
        self.ypad=2
        self.xalign=0.0
        self.yalign=0.8
        self.__width = None
        self.__height = None
        self.__xOffset = None
        self.__yOffset = None
        #self.connect('notify', self.on_changed_property)
        self.connect('clicked', self.on_clicked)
        if not hasattr(self, 'optionlist'):
            pylist = ['This', 'is', 'a test']
            self.optionlist = pylist
        if not hasattr(self, 'selectedoption'):
            self.selectedoption = pylist[0]

    #def on_changed_property(self, widget, value):
        #setattr(self, 'selectedoption', getattr(self, 'optionlist')[0])
        
    def do_get_property(self, id):
        return getattr(self, id.name)

    def do_set_property(self, id, value):
        if not hasattr(self, id.name):
            raise AttributeError, 'unknown property %s' % (id.name)
        setattr(self, id.name, value)

    def on_get_size(self, widget, cellArea):
        """Returns the size needed to render the cell."""
        if self.__width == None or self.__height == None:
            greatest = 0
            for i in self.get_property('optionlist'):
                layout = widget.create_pango_layout(i)
                rect = layout.get_pixel_extents()
                if greatest < rect[1][2]:
                    greatest = rect[1][2]
            
            self.__width= self.xpad*2 + greatest + 22
            self.__height = self.ypad*2 + rect[1][3] + 2
        if self.__xOffset == None or self.__yOffset == None:
            if cellArea:
                self.__xOffset = self.xalign * (cellArea.width - self.__width)
                self.__xOffset = max(self.__xOffset, 0)
                self.__yOffset = self.yalign * (cellArea.height - self.__height)
                self.__yOffset = max(self.__yOffset, 0)
            else:
                self.__xOffset=0
                self.__yOffset=0
                
        return self.__xOffset, self.__yOffset, self.__width, self.__height
    
    def on_activate(self, event, widget, path, backgroundArea, cellArea, flags):
        self.emit('clicked', (widget, event))

    def on_clicked(self, widget, data):
        self.display_options(widget, data)
       
    def alert_changes(self, menuItem, x, y, treeView):
        cell = treeView.get_path_at_pos(x, y)
        path = cell[0]
        model = treeView.get_model()
        changedIter = model.get_iter(path)

        oldValue = self.get_property('selectedoption')
        newValue = menuItem.get_children()[0].get_text()
        if oldValue != newValue:
            self.set_property('selectedoption', newValue)
            self.emit('changed', newValue, changedIter)

    def __compute_menu_position(self, menu):
        """Determine where to place the dropdown menu.

        Relies on pre-setting of self.x, self.y, and self.__height.
        These define the cell's origin and height.
        """
        # x, y, push_in
        return self.x, self.y + self.__height, False

    def display_options(self, widget, data):
        tree=data[0]
        event=data[1]
        currentOption = self.get_property('selectedoption')
        menu=gtk.Menu()
        item = None
        itemList = []
        for entry in self.optionlist:
            item = gtk.RadioMenuItem(item, entry)
            if entry == currentOption:
                item.set_active(True)
            itemList.append(item)
        for item in itemList:
            item.connect('toggled', self.alert_changes,
                    int(event.x), int(event.y), data[0])
            menu.add(item)
            item.show()
        path, column = tree.get_path_at_pos(int(event.x), int(event.y))[:2]
        treeOrigin = tree.get_bin_window().get_origin()
        cellArea = tree.get_cell_area(path, column)
        self.x = treeOrigin[0] + cellArea.x
        self.y = treeOrigin[1] + cellArea.y
        menu.popup(None, None, self.__compute_menu_position, event.button, event.time)
        del(menu)

    def on_render(self, window, widget, backgroundArea, cellArea,
            exposeArea, flags):

        layout = widget.create_pango_layout(self.get_property('selectedoption'))
        xOff, yOff, width, height = self.on_get_size(widget, cellArea)
        if self.get_property('mode') == gtk.CELL_RENDERER_MODE_INERT:
            state = gtk.STATE_INSENSITIVE
        else:
            state = gtk.STATE_NORMAL

        widget.style.paint_box(window,
                state, gtk.SHADOW_OUT,
                cellArea, widget, "Box Name",
                cellArea.x, cellArea.y,
                width, height)
        widget.style.paint_layout(window,
                state, True,
                cellArea, widget, "label",
                cellArea.x + xOff + 3, cellArea.y + yOff,
                layout)
        widget.style.paint_vline(window,
                state,
                cellArea, widget,
                "Separator",
                cellArea.y + yOff + 1, cellArea.y + height,
                cellArea.x+width - 17)
        widget.style.paint_arrow(window,
                state, gtk.SHADOW_OUT,
                cellArea, widget,
                "Name", gtk.ARROW_DOWN, False,
                cellArea.x + width - 13 , cellArea.y + 7,
                10, 10)
gobject.type_register(OptionCellRenderer)
