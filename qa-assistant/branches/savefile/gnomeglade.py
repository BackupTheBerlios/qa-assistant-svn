### Copyright (C) 2002-2003 Stephen Kennedy <steve9000@users.sf.net>

### This program is free software; you can redistribute it and/or modify
### it under the terms of the GNU General Public License as published by
### the Free Software Foundation; either version 2 of the License, or
### (at your option) any later version.

### This program is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.

### You should have received a copy of the GNU General Public License
### along with this program; if not, write to the Free Software
### Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""Utility classes for working with glade files.

"""
import os, sys

import gtk
import gtk.glade
import gnome
import gnome.ui
import gettext

import paths

class Base(object):
    """Base class for all glade objects.

    This class handles loading the xml glade file and connects
    all methods name 'on_*' to the signals in the glade file.

    The handle to the xml file is stored in 'self.xml'. The
    toplevel widget is stored in 'self.widget'.

    In addition it calls widget.set_data("pyobject", self) - this
    allows us to get the python object given only the 'raw' gtk+
    object, which is sadly sometimes necessary.
    """

    def __init__(self, file, root):
        """Load the widgets from the node 'root' in file 'file'.

        Automatically connects signal handlers named 'on_*'.
        """

        self.xml = gtk.glade.XML(file, root, gettext.textdomain() )
        handlers = {}
        for h in filter(lambda x:x.startswith("on_"), dir(self.__class__)):
            handlers[h] = getattr(self, h)
        self.xml.signal_autoconnect( handlers )
        self.widget = getattr(self, root)
        self.widget.set_data("pyobject", self)

    def __getattr__(self, key):
        """Allow glade widgets to be accessed as self.widgetname.
        """
        widget = self.xml.get_widget(key)
        if widget: # cache lookups
            setattr(self, key, widget)
            return widget
        raise AttributeError(key)

    def flushevents(self):
        """Handle all the events currently in the main queue and return.
        """
        while gtk.events_pending():
            gtk.main_iteration();

    def _map_widgets_into_lists(self, widgetnames):
        """Put sequentially numbered widgets into lists.
        
        e.g. If an object had widgets self.button0, self.button1, ...,
        then after a call to object._map_widgets_into_lists(["button"])
        object has an attribute self.button == [self.button0, self.button1, ...]."
        """
        for item in widgetnames:
            setattr(self,item, [])
            list = getattr(self,item)
            i = 0
            while 1:
                key = "%s%i"%(item,i)
                try:
                    val = getattr(self, key)
                except AttributeError:
                    break
                list.append(val)
                i += 1


class Component(Base):
    """A convenience base class for widgets which use glade.
    """

    def __init__(self, file, root):
        Base.__init__(self, file, root)


class GtkApp(Base):
    """A convenience base class for gtk+ apps created in glade.
    """

    def __init__(self, file, root=None):
        Base.__init__(self, file, root)

    def mainloop(self):
        """Enter the gtk main loop.
        """
        gtk.mainloop()

    def quit(self, *args):
        """Signal the gtk main loop to quit.
        """
        gtk.main_quit()


class GnomeApp(GtkApp):
    """A convenience base class for apps created in glade.
    """

    def __init__(self, name, version, file, root):
        """Initialise program 'name' and version from 'file' containing root node 'root'.
        """
        self.program = gnome.program_init(name, version)
        self.program.set_property(gnome.PARAM_APP_DATADIR, paths.datadir)
        self.program.set_property(gnome.PARAM_APP_LIBDIR, paths.libdir)
        self.program.set_property(gnome.PARAM_APP_PREFIX, paths.prefix)
        self.program.set_property(gnome.PARAM_APP_SYSCONFDIR, paths.sysconfdir)

        gladeFile = uninstalled_file(file)
        if gladeFile == None:
            filename = os.path.join(name, file)
            gladeFile = locate_file(gnome.FILE_DOMAIN_APP_DATADIR,
                                    filename)
            if gladeFile == []:
                ### FIXME: Need to use something less generic than this
                raise Exception("Unable to locate %s" % (filename))
            else:
                gladeFile = gladeFile[0]

        GtkApp.__init__(self, gladeFile, root)

        if 0:
            self.client = gnome.ui.Client()
            self.client.disconnect()
            def connected(*args):
                print "CONNECTED", args
            def cb(name):
                def cb2(*args):
                    print name, args, "\n"
                return cb2
            self.client.connect("connect", cb("CON"))
            self.client.connect("die", cb("DIE"))
            self.client.connect("disconnect", cb("DIS"))
            self.client.connect("save-yourself", cb("SAVE"))
            self.client.connect("shutdown-cancelled", cb("CAN"))
            self.client.connect_to_session_manager()


def locate_file(fileDomain, name):
    """Mimic the functionality of gnome_program_locate_file.

    gnome_program_locate_file hasn't been bound into pygtk so do it here.

    Returns: a list of potential files.  The list will be empty if none are
    found
    """
    
    if self.program == None:
        ### FIXME: Need to have a less generic Exception
        raise Exception("GnomeApp must be instantiated before using this method")

    fileList = []
    if name == None or name == "":
        return fileList
    
    if name == os.path.isabs(name):
        if (os.access(name, os.F_OK | os.R_OK)):
            fileList.append(name)
    
    if fileDomain == gnome.FILE_DOMAIN_LIBDIR:
        attrName = gnome.PARAM_GNOME_LIBDIR
        attrRel = ""
    elif fileDomain == gnome.FILE_DOMAIN_DATADIR:
        attrName = gnome.PARAM_GNOME_DATADIR
        attrRel = ""
    elif fileDomain == gnome.FILE_DOMAIN_SOUND:
        attrName = gnome.PARAM_GNOME_DATADIR
        attrRel = "sounds"
    elif fileDomain == gnome.FILE_DOMAIN_PIXMAP:
        attrName = gnome.PARAM_GNOME_DATADIR
        attrRel = "pixmaps"
    elif fileDomain == gnome.FILE_DOMAIN_CONFIG:
        attrName = gnome.PARAM_GNOME_SYSCONFDIR
        attrRel = ""
    elif fileDomain == gnome.FILE_DOMAIN_HELP:
        attrName = gnome.PARAM_GNOME_DATADIR
        attrRel = "gnome/help"
    elif fileDomain == gnome.FILE_DOMAIN_APP_LIBDIR:
        attrName = gnome.PARAM_APP_LIBDIR
        attrRel = ""
    elif fileDomain == gnome.FILE_DOMAIN_APP_DATADIR:
        attrName = gnome.PARAM_APP_DATADIR
        attrRel = ""
    elif fileDomain == gnome.FILE_DOMAIN_APP_SOUND:
        attrName = gnome.PARAM_APP_DATADIR
        attrRel = "sounds"
    elif fileDomain == gnome.FILE_DOMAIN_APP_PIXMAP:
        attrName = gnome.PARAM_APP_DATADIR
        attrRel = "pixmaps"
    elif fileDomain == gnome.FILE_DOMAIN_APP_CONFIG:
        attrName = gnome.PARAM_APP_SYSCONFDIR
        attrRel = ""
    elif fileDomain == gnome.FILE_DOMAIN_APP_HELP:
        attrName = gnome.PARAM_APP_DATADIR
        attrRel = os.path.join("gnome/help",
                self.program.get_property(gnome.PARAM_APP_ID))
    else:
        ### FIXME: Need a less generic exception
        raise Exception("unknown file domain %d" %(fileDomain))

    if (attrName != None):
        dir = self.program.get_property(attrName)
        if (dir == None):
            ### FIXME: Need a less generic exception.
            raise Exception("Directory properties not set correctly.  Cannot locate application specific files.")

        filename = os.path.join(dir, attrRel, name)
        if (os.access(filename, os.F_OK | os.R_OK)):
            fileList.append(filename)

    return fileList

def uninstalled_file(filename):
    """ Check for a file in the directory the program resides in.

    This function is good when you want to allow the program to run before
    it is installed.
    """

    filename = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])),
                                            filename)
    if os.access(filename, os.F_OK | os.R_OK):
        return filename
    else:
        return None

def load_pixbuf(fname, size=0):
    """Load an image from a file as a pixbuf, with optional resizing.
    """
    image = gtk.Image()
    image.set_from_file(fname)
    image = image.get_pixbuf()
    if size:
        aspect = float(image.get_height()) / image.get_width()
        image = image.scale_simple(size, int(aspect*size), 2)
    return image
