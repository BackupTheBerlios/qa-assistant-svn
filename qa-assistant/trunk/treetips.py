# File: treetips.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 6 April, 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
"""A tooltip class for TreeViews
"""
__revision__ = "$Rev$"

import random
import gtk, gobject

class TreeTips(gtk.Widget):
    """ A specialized tooltips widget.

    TreeTips associates a column in a TreeStore with tooltips that will be
    displayed when the mouse is over the row the column is for.  Each row can
    have one treetip.
    """ 
    # The amount of hover time before a treetip pops up (milliseconds)
    DELAY = 500

    def __init__(self, treeview, column):
        """Create a new TreeTips Group.

        Keyword -- arguments:
        treeview -- the treeview the tips are associated with
        column -- the column id the tip text comes from
        """
        
        self.tipWindow = gtk.Window(gtk.WINDOW_POPUP)
        self.tipWindow.set_app_paintable(True)
        self.tipWindow.set_border_width(4)
        self.tipWindow.connect('expose-event', self.__paint_window)
        self.label = gtk.Label()
        self.label.set_line_wrap(True)
        self.label.set_alignment(0.5, 0.5)
        self.tipWindow.add(self.label)
        self.timeoutID = 0
        self.tree = treeview
        self.column = column
        self.path = None
        self.screenWidth = gtk.gdk.screen_width()
        self.screenHeight = gtk.gdk.screen_height()
        self.tree.connect("leave-notify-event", self.__tree_leave_notify)
        self.tree.connect("motion-notify-event", self.__tree_motion_notify)

    def __paint_window(self, window, event):
        self.tipWindow.style.paint_flat_box(self.tipWindow.window,
                gtk.STATE_NORMAL, gtk.SHADOW_OUT, None, self.tipWindow,
                "tooltip", 0, 0, -1, -1)
        
    def __tree_leave_notify(self, tree, event):
        """Hide tooltips when we leave the tree."""

        self.timeoutID = 0
        self.path = None
        self.tipWindow.hide()

    def __tree_motion_notify(self, tree, event):
        """Decide which tooltip to display when we move within the tree."""

        self.tipWindow.hide()
        self.path = None
        timeoutID = random.randint(1, 10000)
        self.timeoutID = timeoutID
        gobject.timeout_add(self.DELAY, self.__treetip_show, tree,
                event.x, event.y, timeoutID)

    def __treetip_show(self, tree, xEvent, yEvent, ID):
        if self.timeoutID != ID:
            return False
        pathReturn = self.tree.get_path_at_pos(xEvent, yEvent)
        model = self.tree.get_model()
        if pathReturn == None:
            self.path = None
        elif self.path != pathReturn[0]:
            self.path = pathReturn[0]
            iter = model.get_iter(self.path)
            text = model.get_value(iter, self.column)
            self.label.set_text(text)
            x, y = self.label.size_request()
            self.tipWindow.resize(x, y)
            windowWidth, windowHeight = self.tipWindow.get_size()
            cellInfo = tree.get_cell_area(self.path, pathReturn[1])
            x, y = self.__compute_tooltip_position(cellInfo, windowWidth, windowHeight)
            self.tipWindow.move(int(x), int(y))
            self.tipWindow.show_all()

        return False

    def __compute_tooltip_position(self, cellInfo, popupWidth, popupHeight):
        """Figures out where the tooltip should be placed on the page

        [p] = pointer
        x =      [p]
             +---------+
        (half on each side)

        y =      [p]
            +------------+
            |____________|
        If it fits else:
            +------------+
            |____________|
                 [p]
        """

        xOrigin, yOrigin = self.tree.get_bin_window().get_origin()
        x = xOrigin + cellInfo.x + cellInfo.width/2 - popupWidth/2
        if x < 0:
            x = 0
        elif x + popupWidth > self.screenWidth:
            x = self.screenWidth - popupWidth

        y = yOrigin + cellInfo.y + cellInfo.height + 3
        if y + popupHeight > self.screenHeight:
            y = yOrigin + cellInfo.y - 3 - popupHeight
            if y < 0:
                y = 0

        return x, y

    def enable(self):
        """Enable showing of tooltips"""
        pass

    def disable(self):
        """Disable showing tooltips"""
        pass
        
