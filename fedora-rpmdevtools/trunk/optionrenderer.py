# File: optionrenderer.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 10 Mar 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Description:
# Id: $Id$
"""Cell Renderer to display a list of options that the user may select from.
"""
__revision__ = "$Revision$"

import string
import gtk, gobject

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
        #self.connect('notify', self.on_changed_property)
        self.connect('clicked', self.on_clicked)
        if not hasattr(self, 'optionlist'):
            pylist = ['This', 'is', 'a test']
            setattr(self, 'optionlist', pylist)
        if not hasattr(self, 'selectedoption'):
            setattr(self, 'selectedoption', pylist[0])

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
        greatest = 0
        for i in self.get_property('optionlist'):
            layout = widget.create_pango_layout(i)
            rect = layout.get_pixel_extents()
            if greatest < rect[1][2]:
                greatest = rect[1][2]
            
        calcWidth= self.xpad*2 + greatest + 22
        calcHeight = self.ypad*2 + rect[1][3] + 2
        if cellArea:
            xOffset = self.xalign * (cellArea.width - calcWidth)
            xOffset = max(xOffset, 0)
            yOffset = self.yalign * (cellArea.height - calcHeight)
            yOffset = max(yOffset, 0)
        else:
            xOffset=0
            yOffset=0
        return xOffset, yOffset, calcWidth, calcHeight
    
    def on_activate(self, event, widget, path, backgroundArea, cellArea, flags):
        self.emit('clicked', (widget, event))

    def on_start_editing(self, event, widget, path, backgroundArea, cellArea, flags):
        print "editing"
        pass

    def on_clicked(self, widget, data):
        self.display_options(widget, data)
       
    def alert_changes(self, menuItem, x, y, treeView):
        cell = treeView.get_path_at_pos(x, y)
        path = cell[0]
        model = treeView.get_model()
        iter = model.get_iter(path)

        oldValue = self.get_property('selectedoption')
        newValue = menuItem.get_children()[0].get_text()
        if oldValue != newValue:
            self.set_property('selectedoption', newValue)
            self.emit('changed', newValue, iter)

    ### FIXME: Unused for now.  Eventually we should render the menu over the
    # combobox to look correct.  Then add this function as the third argument
    # to the display_options::menu.popup() call
    def menu_position(self, menu, unknown=None, data=None):
        return 0, 0, 0

    def display_options(self, widget, data):
        event=data[1]
        currentOption = self.get_property('selectedoption')
        menu=gtk.Menu()
        item = None
        itemList = []
        for entry in getattr(self, 'optionlist'):
            item = gtk.RadioMenuItem(item, entry)
            if entry == currentOption:
                item.set_active(True)
            itemList.append(item)
        for item in itemList:
            item.connect('toggled', self.alert_changes,
                    event.x, event.y, data[0])
            menu.add(item)
            item.show()
        
        menu.popup(None, None, None, event.button, event.time)
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