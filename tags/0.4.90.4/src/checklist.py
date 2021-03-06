# File: checklist.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 04 Mar 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Description: Class file to load a description of a checklist into internal
# structures.
# Id: $Id$
'''
Class file to load a description of a checklist into python structures.
'''

__revision__ = '$Rev$'

import re
import os
import sys

import libxml2
import gtk
import gnome
import gobject
import gconf

from qaglobals import *
import error
import properties
import functions

# TreeStore entries displayed on the screen
(ISITEM,     # Entry is an item as oppoed to a category
 DISPLAY,    # Write the output to the review
 SUMMARY,    # Unique title for the entry
 DESC,       # Long description of what to do to verify the entry
 RESOLUTION, # Current resolution
 OUTPUT,     # Current resolution's output
 RESLIST,    # Python list of possible resolutions
 OUTPUTLIST, # Python hash of outputs keyed to resolution
 TEST        # Python class that holds any automated test information
 ) = range(9)

class CheckList (gtk.TreeStore):
    '''Holds the data associated with the checklist.

    Attributes:
    name -- Checklist's name
    revision -- Revision of the checklist file
    type -- Type of the checklist file
    resolution -- Resolution of the CheckList.
    publicID -- Public identifier for the checklist's XML DTD
    canonicalURL -- Canonical URL for the checklist's XML DT
    entries -- Mapping of names to iters of checklist entries
    customItemsIter -- gtk.TreeIter pointing to the category we are adding
                       custom items to

    Private Attributes:
    __unspan -- Regex to remove <span> pango tags from a string.  Saved so the
                code doesn't have to recompile the regex every time.
    
    Special Purpose Attributes (These should translate into a properties map
    or similar in the future):
    SRPM -- SRPM object having information about the SRPM we are reviewing
    ticketURL -- URL to get to the ticket for this checklist
    
    Obsolete Attributes (Certain functionality that is being phased out
    depends on these.  As soon as the functionality goes, these can go.)
    baseFilename -- File that the checklist was started from.  Goes away when
                    we unify savefile and checklist if we don't find another
                    use for it.  (Currently saved in the savefile.  Need to
                    remove.)
    
    * Note: Some attributes should be gproperties.  However, there is a problem
    currently with gproperties and the initialization of gtk.TreeStore classes.
    Have to make them simple python attibutes for now and create our own
    signals instead of using gproperties with the notify signal.

    The CheckList class is a subclass of gtk.TreeModel and has all the methods
    that the gtk.TreeModel class has for manipulating the data it save.  It
    overrides the constructor to make a much more directed model that
    implements one data set.  Saving the state of the checklist's data
    saves the modified data in the TreeModel along with a reference
    to the checklist we're operating upon.
    '''

    ### FIXME: These are ripe for becoming read-only gobject properties
    # checklist identifying strings
    formatVersion = '0.3'

    publicID = '-//BaderWare//DTD QA Assistant Checklist File ' \
            + formatVersion + '//EN'
    canonicalURL = 'http://qa-assistant.sf.net/dtds/checklist/' \
            + formatVersion + '/checklist.dtd'

    # Gobject signals
    __gsignals__ = {
        'resolution-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_BOOLEAN,
                (gobject.TYPE_STRING,)),
        'changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                (gobject.TYPE_PYOBJECT,))
    }

    class __Entry:
        '''Private class.  Holds entry information until ready to output.'''

    class __Test:
        '''Information related to automated tests embedded in the XML files.
        
        This class is meant to be invoked by the CheckList class.  It will be
        wrapped in CheckList methods `run_test(SUMMARY)` and `run_all_tests()`

        It won't be used directly by other programs because it is assumed that
        getting properties from the CheckList into the Test would be harder.
        If this is not the case, this class may become public and outside code
        may use its interface directly.
        '''
        def run(self):
            '''
    
            Returns: Tuple of Resolution string and Output for the string.  The
                     output may be None.
            '''
            pass

    def __init__(self, path):
        ''' Create a new CheckList

        Attributes:
        path -- full pathname of the checklist file we're implementing.

        Creates a new CheckList.
        '''
        self.filename = path # Filename of the checklist we're implementing
        self.fileLoadDir = os.path.dirname(path) # Directory we loaded the 
                                                 # checklist from
        self.resolution = 'Needs-Reviewing' # Resolution of the checklist
        self.functionHash = None # Hash of the functions file
        self.functionHashType = None # Type of the hash (sha1, md5, etc)
        self.functionFile = None # File containing the functions
        # Properties available on the checklist
        self.properties = properties.Properties()
        self.customItemsIter = None # Iter to the custom items category
        self.colors = {}
        self.__unspan = re.compile(r'([^<]*)(<span[^>]*>)?([^<]*)(</span>)?(.*)')
        self.colorRE = re.compile('^#[A-Fa-f0-9]{6}$')
        self.gconfClient = gconf.client_get_default()

        self.gconfClient.add_dir(GCONFPREFIX, gconf.CLIENT_PRELOAD_NONE)
        self.__init_colors('/display/pass-color')
        self.__init_colors('/display/fail-color')
        self.__init_colors('/display/minor-color')
        self.__init_colors('/display/notes-color')
        key = GCONFPREFIX + '/display/no-auto-display'
        try:
            self.noAutoDisplay = self.gconfClient.get_bool(key)
        except gobject.GError:
            self.noAutoDisplay = (
                    self.gconfClient.get_default_from_schema(key).get_bool())
        self.gconfClient.notify_add(key, self.__change_auto_display)
        
        libxml2.registerErrorHandler(self.__no_display_parse_error, None)
        ctxt = libxml2.newParserCtxt()
        try:
            checkFile = ctxt.ctxtReadFile(path, None, libxml2.XML_PARSE_DTDVALID)
        except libxml2.treeError:
            raise error.InvalidChecklist('%s was not an XML file' % (path))

        if not ctxt.isValid():
            checkFile.freeDoc()
            raise error.InvalidChecklist('File does not validate against '
                    'the checklist DTD')

        root = checkFile.getRootElement()
        if root.name != 'checklist':
            checkFile.freeDoc()
            raise error.InvalidChecklist('File is not a valid checklist '
                    'policy file')
        if root.prop('version') != self.formatVersion:
            checkFile.freeDoc()
            raise error.InvalidChecklist('Checklist file is not a known '
                    'version')
       
        # Extract the name and revision of the CheckList
        self.name = root.prop('name')
        if not self.name:
            checkFile.freeDoc()
            raise error.InvalidChecklist('Checklist file does not specify '
                    'a name for itself')
        self.revision = root.prop('revision') or '0'

        summary = root.xpathEval2('/checklist/summary')
        if summary:
            self.summary = summary[0].content
        else:
            checkFile.freeDoc()
            raise error.InvalidChecklist('Checklist does not have a summary')

        # Create GtkTreeModel struct to store info in.
        gtk.TreeStore.__init__(self, gobject.TYPE_BOOLEAN,
                gobject.TYPE_BOOLEAN,
                gobject.TYPE_STRING,
                gobject.TYPE_STRING,
                gobject.TYPE_STRING,
                gobject.TYPE_STRING,
                gobject.TYPE_PYOBJECT,
                gobject.TYPE_PYOBJECT,
                gobject.TYPE_PYOBJECT)
        base = root.xpathEval2('/checklist/base')
        if base:
            # We are loading a savefile.  Just load the base info.
            self.baseName = base[0].prop('name')
            self.baseRevision = base[0].prop('revision')
            self.baseFilename = base[0].content
            self.revision = int(self.revision)
        else:
            # We are loading an original checklist definition.  Set its values
            # as the base and set the CheckList info to good values.
            self.baseName = self.name
            self.baseRevision = self.revision
            self.baseFilename = path
            self.filename = None
            self.revision = 0
        
        # Extract properties from the CheckList file
        props = root.xpathEval2('/checklist/properties/property')
        for p in props:
            propChild = p.children
            propEntry = properties.PropEntry()
            propEntry.valueType = p.prop('type')
            while propChild:
                if propChild.name == 'require':
                    propEntry.propType = propChild.prop('type')
                    requireChild = propChild.children
                    while requireChild:
                        if requireChild.name == 'arg':
                            propEntry.args.append(requireChild.content)
                        elif requireChild.name == 'function':
                            propEntry.function = requireChild.content
                        requireChild = requireChild.next
                elif propChild.name == 'value':
                    propEntry.value = propChild.content
                propChild = propChild.next
            # Set the property
            self.properties[p.prop('name')] = propEntry

        # Extract functions for the QA menu
        funcs = root.xpathEval2('/checklist/functions')
        if funcs:
            self.functionHash = funcs[0].prop('hash')
            self.functionHashType = funcs[0].prop('hashtype')
            self.functionFile = funcs[0].content
            self.functions = self._load_functions()
        else:
            self.functions = functions.BaseQAFunctions(self)
        del funcs
        
        # Record each category as a toplevel in the tree
        categories = root.xpathEval2('/checklist/category')
        self.entries = {}
        for category in categories:
            newCat = self.append(None)
            gtk.TreeStore.set(self, newCat,
                    ISITEM, False,
                    RESLIST, ['Needs-Reviewing', 'Pass', 'Fail'],
                    RESOLUTION, 'Needs-Reviewing',
                    OUTPUT, '',
                    OUTPUTLIST, {'Needs-Reviewing': '',
                                 'Pass': '', 'Fail': ''},
                    SUMMARY, category.prop('name'),
                    TEST, None)
            self.entries[category.prop('name').lower()] = newCat

            # Entries are subheadings
            node = category.children
            while node:
                if node.name == 'description':
                    # Set DESCRIPTION of the heading
                    desc = ' '.join(node.content.split())
                    gtk.TreeStore.set(self, newCat, DESC, desc)
                elif node.name == 'entry':
                    entry = self.__xml_to_entry(node)
                    entryIter = self.append(newCat)
                    gtk.TreeStore.set(self, entryIter,
                            ISITEM, True,
                            DISPLAY, entry.display,
                            SUMMARY, entry.name,
                            TEST, entry.test,
                            DESC, entry.desc)
                    self.entries[entry.name.lower()] = entryIter
                    
                    # Construct the resolution from multiple states
                    outputList = {'Needs-Reviewing': ''}
                    resolutionList = ['Needs-Reviewing']
                    for i in range(len(entry.states)):
                        name = entry.states[i]['name']
                        # Order is important: We pangoize as things enter
                        # OUTPUT, not OUTPUTLIST.
                        outputList[name] = entry.states[i]['output']
                        if name != 'Needs-Reviewing':
                            resolutionList.append(entry.states[i]['name'])
                    
                    res = entry.state
                    gtk.TreeStore.set(self, entryIter,
                            RESLIST, resolutionList,
                            OUTPUTLIST, outputList,
                            RESOLUTION, res,
                            OUTPUT, self.pangoize_output(res,
                                outputList[res]))
                else:
                    # DTD validation should make this ignorable.
                    pass
                  
                node = node.next

        checkFile.freeDoc()

        ### FIXME: Merge code:  This is pretty close to what we have in:
        # __check_resolution().  We could potentially merge these two pieces
        # of code together.
        category = self.get_iter_root()
        catIter = category
        while catIter:
            entryIter = self.iter_children(catIter)
            newRes = 'Pass'
            while entryIter:
                res = self.get_value(entryIter, RESOLUTION)
                if res == 'Fail':
                    newRes = 'Fail'
                    break
                elif res == 'Needs-Reviewing':
                    newRes = 'Needs-Reviewing'
                entryIter = self.iter_next(entryIter)
            gtk.TreeStore.set(self, catIter, RESOLUTION, newRes)
            catIter = self.iter_next(catIter)
        # Instead of code we could have:
        # self.__check_resolution(category, 'Pass') 
        newRes = 'Pass'
        while category:
            res = self.get_value(category, RESOLUTION)
            if res == 'Fail':
                newRes = 'Fail'
                break
            elif res == 'Needs-Reviewing':
                newRes = 'Needs-Reviewing'
            category = self.iter_next(category)
        self.resolution = newRes
        self.properties.connect('changed', self._prop_change)

    def _prop_change(self, *extras):
        self.emit('changed', extras)

    def add_entry(self, summary, item=None, display=None,
            desc=None, resolution=None, output=None,
            resList=None, outputList=None):
        '''Adds new items to the checklist.
        
        Arguments:
        summary -- Summary of problem (also its key.)
        
        Keyword arguments:
        item -- entry is an item rather than a category. (default True)
        display -- display the entry in output review. (default True)
        desc -- long description about how to determine if the item has
                passed or failed the test. (default None)
        resolution -- state that the entry is in. (default Needs-Reviewing)
        output -- output string for the entry. (default None)
        resList -- list of valid resolutions. (default Needs-Reviewing, Pass,
                   Fail, Non-Blocker, Not-Applicable)
        outputList -- dict of output strings for each resList item. (default
                      None for each resolution in resList)

        Caveats:
        * outputList[resolution] is set to output even if it already has a
          value.
        '''

        # Make sure this entry isn't already listed.
        sumLow = summary.lower()
        if self.entries.has_key(sumLow):
            raise error.DuplicateItem, ('%s is already present in the'
                    ' checklist.' % (self.entries[sumLow]))

        # Set up all the default values.
        if item == None:
            item = True
        if display == None:
            display = True
        output = output or ''
        desc = desc or None
        resList = resList or ['Needs-Reviewing', 'Pass', 'Fail',
            'Non-Blocker', 'Not-Applicable']
        resolution = resolution or resList[0]
        if resolution not in resList:
            raise error.InvalidResolution, ('%s is not a resolution from the'
                    ' resolution List' % (resolution))

        # Make sure the outputList matches with the resList
        if not outputList:
            outputList = {}
            for res in resList:
                outputList[res] = ''
        else:
            outKeysList = outputList.keys()
            for res in resList:
                if res not in outKeysList:
                    outputList[res] = ''
        outputList[resolution] = output
       
        if self.customItemsIter:
            newItem = self.append(self.customItemsIter)
        else:
            self.customItemsIter = self.append(None)
            if sumLow == 'custom checklist items':
                newItem = self.customItemsIter
            else:
                # Create the 'Custom Checklist Items' category
                self.set(self.customItemsIter,
                        SUMMARY, 'Custom Checklist Items',
                        ISITEM, False,
                        RESLIST, ['Needs-Reviewing', 'Pass', 'Fail'],
                        RESOLUTION, 'Needs-Reviewing',
                        OUTPUT, '',
                        OUTPUTLIST, {'Needs-Reviewing': '',
                                     'Pass': '', 'Fail': ''},
                        DESC, "Review items that you have comments on even " \
                              "though they aren't on the standard checklist.",
                        TEST, None)
                newItem = self.append(self.customItemsIter)
                self.entries['custom checklist items'] = self.customItemsIter
        
        # Set up the new item
        self.set(newItem,
                SUMMARY, summary,
                DESC, desc,
                ISITEM, item,
                DISPLAY, display,
                RESOLUTION, resolution,
                OUTPUT, output,
                RESLIST, resList,
                OUTPUTLIST, outputList,
                TEST, None)
        self.entries[sumLow] = newItem

    def publish(self, filename=None):
        '''Saves the current state of the `CheckList` into a savefile.
        
        Attributes:
        filename -- File to save the checklist in. (default self.filename)
        
        Saves the CheckList information into the filename.
        '''
        
        self.filename = filename or self.filename
        if not self.filename:
            raise error.CannotAccessFile('No filename given to save to.')
        # Create the xml DOM conforming to our save DTD
        doc = libxml2.newDoc('1.0')
        doc.createIntSubset('checklist', self.publicID,
                self.canonicalURL)
        
        # Output root node
        root = doc.newChild(None, 'checklist', None)
        root.setProp('version', self.formatVersion)
        if not self.name.endswith(' Savefile'):
            self.name += ' Savefile'
        root.setProp('name', self.name)
        self.revision += 1
        root.setProp('revision', str(self.revision))
       
        # Output summary node
        root.newChild(None, 'summary', self.summary)

        # Output base checklist information
        node = root.newTextChild(None, 'base', self.baseFilename)
        node.setProp('name', self.baseName)
        node.setProp('revision', self.baseRevision)
       
        # Output properties we're concerned with
        if self.properties:
            props = root.newChild(None, 'properties', None)
            for propName in self.properties.keys():
                prop = self.properties[propName]
                node = props.newChild(None, 'property', None)
                node.setProp('name', propName)
                node.setProp('type', prop.valueType)
                require = node.newChild(None, 'require', None)
                require.setProp('type', prop.propType)
                for arg in prop.args:
                    require.newTextChild(None, 'arg', arg)
                if prop.function:
                    require.newTextChild(None, 'function', prop.function)
                if prop.value:
                    node.newTextChild(None, 'value', prop.value)

        # Output functions
        if self.functionFile:
            funcs = root.newTextChild(None, 'functions', self.functionFile)
            funcs.setProp('hash', self.functionHash)
            funcs.setProp('hashtype', self.functionHashType)
        
        # Output entries
        self.foreach(self.__create_entry, root)

        # Write the file
        doc.saveFormatFileEnc(self.filename, 'UTF-8', True)
        doc.freeDoc()

    def unpangoize_output(self, output):
        '''Removes pango tags and unescapes pango special chars from output.

        Arguments:
        output -- output string to remove pango from.

        This does the opposite of pangoize_output.  It removes pango span
        tags which provide colorization to the output strings and replaces
        escaped pango special chars with their ASCII character.

        Returns: string with pango tags removed and special chars resotred.
        '''
        
        # Remove the span tags
        output = self.__unspan.match(output).expand(r'\g<1>\g<3>\g<5>')
        # Unescape special chars
        output = output.replace('&amp;', '&')
        output = output.replace('&lt;', '<')
        output = output.replace('&gt;', '>')

        return output

    def pangoize_output(self, resolution, output):
        '''Colorize the output based on the resolution.
        
        Arguments:
        resolution -- state of review that the output string applies to.
        output -- the output string to colorize.

        Returns: the modified output string.
        '''

        output = output.replace('&', '&amp;')
        output = output.replace('<', '&lt;')
        output = output.replace('>', '&gt;')

        if resolution == 'Fail':
            color = self.colors['/display/fail-color']
        elif resolution == 'Non-Blocker':
            color = self.colors['/display/minor-color']
        elif resolution == 'Pass':
            color = self.colors['/display/pass-color']
        else:
            color = self.colors['/display/notes-color']
        if color:
            output = ('<span foreground="' + color + '">' +
                    output + '</span>')
        return output
  
    def set(self, row, *columnValues):
        '''Override the base set method to specify special actions if the
        column is for RESOLUTION.
        '''
        newValues = []
        for listIndex in range(0, len(columnValues), 2):
            if columnValues[listIndex] == RESOLUTION:
                res = columnValues[listIndex+1]
                gtk.TreeStore.set(self, row,
                        RESOLUTION, res)
                # Change the OUTPUT as well
                outputlist = self.get_value(row, OUTPUTLIST)
                if outputlist:
                    gtk.TreeStore.set(self, row,
                            OUTPUT, self.pangoize_output(res, outputlist[res]))

                # Auto display to review if it's a fail
                if (not self.noAutoDisplay) and (res == 'Fail' or
                        res == 'Non-Blocker'):
                    gtk.TreeStore.set(self, row, DISPLAY, True)

                self.__check_resolution(row, res)
            elif columnValues[listIndex] == OUTPUT:
                out = columnValues[listIndex+1]
                out = self.pangoize_output(
                        self.get_value(row, RESOLUTION), out)
                newValues.extend((columnValues[listIndex], out))
            else:
                newValues.extend((columnValues[listIndex],
                    columnValues[listIndex+1]))
 
        # Set the new data
        gtk.TreeStore.set(self, row, *newValues)
        self.emit('changed', row)

    #
    # Helpers to manage display of the checklist
    #
    
    def __change_auto_display(self, client, connectID, entry, extra):
        '''Changes whether we auto-display the review when it is negative.

        :client: gconf client the change occurred on.
        :connectID: id for the gconf connection.
        :entry: gconf entry that has been changed.
        :extra: user data.  None taken.
        '''
        if entry.value and entry.value.type == gconf.VALUE_BOOL:
            self.noAutoDisplay = entry.value.get_bool()
        else:
            self.noAutoDisplay = False
       
    ### FIXME: The three color functions really belong in the checkview
    # Rather than here.  They involve seting and changing the colors for
    # displaying the data....
    def __init_colors(self, colorKey):
        '''Initialize the colors from GConf.

        Arguments:
        :colorKey: gconf key for the color minus the application prefix.

        Initializes the colors for displaying the checklist from gconf into
        our private variables.
        '''
        key = GCONFPREFIX + colorKey
        self.gconfClient.notify_add(key, self.__color_changed, colorKey)
        try:
            color = self.gconfClient.get_string(key)
        except gobject.GError:
            color = self.gconfClient.get_default_from_schema(key).get_string()
        if color and self.colorRE.match(color):
            self.colors[colorKey] = color
        else:
            self.colors[colorKey] = (
                    self.gconfClient.get_default_from_schema(key).get_string())

    def __color_changed(self, client, connectID, entry, colorKey):
        '''Changes a color when it is changed in GConf.

        :client: gconf client the change occurred on.
        :connectID: id for the gconf connection.
        :entry: gconf entry that has been changed.
        :colorKey: which color we're saving into.
        '''
        self.colors[colorKey] = '#000000'
        if entry.value and entry.value.type == gconf.VALUE_STRING:
            color = entry.value.get_string()
            if self.colorRE.match(color):
                self.colors[colorKey] = color
        if colorKey == '/display/fail-color':
            resChanged = 'Fail'
        elif colorKey == '/display/pass-color':
            resChanged = 'Pass'
        elif colorKey == '/display/minor-color':
            resChanged = 'Non-Blocker'
        else:
            resChanged = 'Needs-Reviewing'
        self.foreach(self.__change_color, resChanged)

    def __change_color(self, model, path, treeIter, resChanged):
        '''Changes the color of an output string.

        :model: Tree model we're operating on.
        :path: Path to the row we're operating on
        :treeIter: Iter pointing to the row we're operating on.
        :resChanged: New resolution.

        This function is meant to be called from a gtk.TreeModel.foreach.
        '''
        res = model.get_value(treeIter, RESOLUTION)
        if res == resChanged:
            outList = model.get_value(treeIter, OUTPUTLIST)
            out = outList[res]
            if out:
                out = self.pangoize_output(res, out)
                gtk.TreeStore.set(model, treeIter, OUTPUT, out)
        elif resChanged == 'Needs-Reviewing' and res == 'Not-Applicable':
            outList = model.get_value(treeIter, OUTPUTLIST)
            out = outList[res]
            if out:
                out = self.pangoize_output(res, out)
                gtk.TreeStore.set(model, treeIter, OUTPUT, out)
        return False

    def __check_resolution(self, changedRow, newValue):
        '''Checks whether to change a category's resolution.
        
        Arguments:
        :changedRow: The entry row that has changed.
        :newValue: The new value of the row.

        Called when a row's resolution has changed.  We check whether the
        parent of the resolution needs to have its resolution changed as well.
        '''
        # Load category information to check if it needs updating.
        category = self.iter_parent(changedRow)
        if category:
            # We are checking through all the entries of a single category
            catRes = self.get_value(category, RESOLUTION)
            entryIter = self.iter_children(category)
        else:
            # We are checking through the categories of a checklist.
            catRes = self.resolution
            entryIter = self.get_iter_root()

        # Check if the change makes the overall review into a pass or fail
        if newValue == 'Fail':
            # Unless it's already set to Fail, we'll change it.
            if catRes == 'Fail':
                return
        elif newValue == 'Needs-Reviewing':
            # If there's no entries for Fail, we'll change to Needs-Reviewing
            if catRes == 'Needs-Reviewing':
                return
            if catRes != 'Pass':
                while entryIter:
                    nodeRes = self.get_value(entryIter,
                            RESOLUTION)
                    if nodeRes == 'Fail':
                        return
                    entryIter = self.iter_next(entryIter)
        else:
        # These are the values we want here.  They are also the only ones
        # left, therefore we can use a simple else.
        #elif (newValue == 'Pass' or newValue == 'Not-Applicable' or 
        #        newValue == 'Non-Blocker'):
            # Unless another entry is Fail or Needs-Reviewing, change to Pass
            newValue = 'Pass'
            while entryIter:
                nodeRes = self.get_value(entryIter, RESOLUTION)
                if nodeRes == 'Needs-Reviewing':
                    if catRes == 'Needs-Reviewing':
                        return
                    newValue = 'Needs-Reviewing'
                elif nodeRes == 'Fail':
                    return
                entryIter = self.iter_next(entryIter)

        if category:
            self.set(category, RESOLUTION, newValue)
        else:
            self.resolution = newValue
            self.emit('resolution-changed', newValue)

    def _load_functions(self):
        '''Load functions file if it's valid.

        Check that the functions file is valid.  If so, import it and return
        the function object.
        '''
        app = gnome.program_get()
        try:
            filename = app.locate_file(gnome.FILE_DOMAIN_DATADIR,
                    os.path.join(PROGRAMNAME, 'data', self.functionFile), True)
        except AttributeError:
            # We were unable to get a gnome program.  Try to find a
            # functions file in the same directory as the checklist.
            filename = os.path.join(self.fileLoadDir, self.functionFile)
        else:
            try:
                filename = filename[0]
            except IndexError:
                ### FIXME: This pathway is untested.  Won't be tested until
                # we support checklists in user defined locations.
                # (ie: User specifies to load custom checklist from home
                # directory.  Custom checklist has a function file in that
                # directory.)
                filename = os.path.join(self.fileLoadDir, self.functionFile)
        try:
            functionFile = file(filename)
        except IOError:
            raise error.InvalidFunctions, ('Unable to open the functions'
                    ' file %s.' % (filename))

        # Make sure functionFile matches the hash.
        if self.functionHashType == 'sha1':
            import sha as thehash
        elif self.functionHashType == 'md5':
            import md5 as thehash
        elif self.functionHashType == 'nullhash':
            thehash = NullHash()
        else:
            raise error.UnknownHashType, ('The checklist says the functions'
                    ' file has hash %s of type %s which is an unknown type' %
                    (self.functionHash, self.functionHashType))
        hasher = thehash.new(''.join(functionFile.readlines()))
        if hasher.hexdigest() != self.functionHash:
            raise error.InvalidFunctions, ('Function file %s does not match'
                    ' recorded hash' % (self.functionFile))
        # If so, load the file
        sys.path.append(os.path.dirname(filename))
        exec ('import ' + self.functionFile[0:-3] + ' as functions')
        return functions.QAFunctions(self)
    #
    # Helpers to read a checklist
    #
    
    def __no_display_parse_error(self, ctx, string):
        """Disable Displaying parser errors."""
        pass

    def __xml_to_entry(self, node):
        """Converts an entry node from an XML DOM into a python data structure.

        Keyword -- arguments:
        node -- an entry node to convert.

        Returns: an entry data structure.
        """
        entry = self.__Entry()
        entry.test = None

        entry.name = node.prop('name')
        entry.state = node.prop('state')
        if node.prop('display') == 'true':
            entry.display = True
        else:
            entry.display = False
        fields = node.children
        while fields:
            if fields.name == 'states':
                state = fields.children
                n = 0
                entry.states = []
                while state:
                    if state.name == 'state':
                        entry.states.append({'name' : state.prop('name')})
                        output = ' '.join(state.content.split())
                        entry.states[n]['output'] = output
                        if entry.states[n]['output'].strip() == '':
                            entry.states[n]['output'] = (entry.name + ': ' 
                                    + state.prop('name'))
                        n += 1
                    else:
                        # DTD validation should catch things that aren't
                        # supposed to end up here.
                        pass
                    state = state.next
            elif fields.name == 'description':
                desc = ' '.join(fields.content.split())
                entry.desc = desc
            elif fields.name == 'test':
                testFields = fields.children
                entry.test = self.__Test()
                entry.test.arguments = []
                while testFields:
                    if testFields.name == 'argument':
                        argument = testFields.content
                        if not self.properties.has_key(argument):
                            # Argument was invalid substitute this test for
                            # the real one so the user can be alerted to the
                            # fact that the test did not run correctly.
                            entry.test.code = '''import sys
print 'Automated test error: "%s" is an invalid argument because it is not a property name'
sys.exit(4)
''' % (argument)
                            entry.test.language = 'python' 
                            entry.test.minlangver = None
                            entry.test.maxlangver = None
                            break

                        entry.test.arguments.append(argument)
                    elif testFields.name == 'code':
                        entry.test.language = testFields.prop('language') \
                                or None
                        entry.test.minlangver = testFields.prop('minlangver') \
                                or None
                        entry.test.maxlangver = testFields.prop('maxlangver') \
                                or None
                        entry.test.code = testFields.content
                    else:
                        # DTD validation should catch things that aren't
                        # supposed to end up here.
                        pass
                    testFields = testFields.next
            else:
                # DTD validation should prevent anything uwanted from
                # ending up here.
                pass
            fields = fields.next

        return entry
    
    #
    # Helpers to create a checklist
    #
    
    def __create_entry(self, tree, path, entryIter, root):
        '''Create an entry node and add it to the document.
        
        Attributes:
        tree -- treemodel (synonymous to self)
        path -- current path in the tree
        entryIter -- current iter in the tree
        root -- root of the xml entries node we're adding values to
        
        Meant to be used by a gtk.TreeModel.foreach().  This function
        transforms the rows of data in the TreeModel into entries output
        to the XML savefile.
        '''

        # Check if we're adding an entry or a category.
        if tree.get_value(entryIter, ISITEM):
            # Entry node
            entry = root.lastChild().newChild(None, 'entry', None)
            if tree.get_value(entryIter, DISPLAY):
                entry.setProp('display', 'true')
            else:
                entry.setProp('display', 'false')
            entry.setProp('state', tree.get_value(entryIter, RESOLUTION))

            # state nodes
            resolutions = tree.get_value(entryIter, RESLIST)
            outputs = tree.get_value(entryIter, OUTPUTLIST)
            states = entry.newChild(None, 'states', None)
            for res in resolutions:
                content = outputs[res]
                state = states.newTextChild(None, 'state', content)
                state.setProp('name', res)
                
            # test node
            test = tree.get_value(entryIter, TEST)
            if test:
                testNode = entry.newChild(None, 'test', None)
                for arg in test.arguments:
                    testNode.newTextChild(None, 'argument', arg)
                codeNode = testNode.newTextChild(None, 'code', test.code)
                if test.language:
                    codeNode.setProp('language', test.language)
                if test.minlangver:
                    codeNode.setProp('minlangver', test.minlangver)
                if test.maxlangver:
                    codeNode.setProp('maxlangver', test.maxlangver)
        else:
            entry = root.newChild(None, 'category', None)

        # Common to both categories and entries:
        entry.setProp('name', tree.get_value(entryIter, SUMMARY))
        entry.newTextChild(None, 'description',
                tree.get_value(entryIter, DESC))

gobject.type_register(CheckList)

class NullHash:
    def __init__(self):
        pass
    def new(self, *extra):
        return self
    def hexdigest(self, *extra):
        return '@@hash@@'
