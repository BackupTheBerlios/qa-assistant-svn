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

import string
import re

import libxml2
import gtk
import gobject

import error

ISITEM=0     # Entry is an item as opposed to category
DISPLAY=1    # Write the output to the review
SUMMARY=2    # Unique title for the entry
DESC=3       # Long description of what to do to verify the entry
RESOLUTION=4 # Current resolution
OUTPUT=5     # Current resolution's output
RESLIST=6    # Python list of possible resolutions
OUTPUTLIST=7 # Python hash of outputs keyed to resolution
TEST=8       # Python class that holds any automated test information

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
    addPaths -- Dictionay holding paths we're in the process of adding to the
                tree until we have a key value so we can add it to the
                `entries` lookup hash

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

    # checklist identifying strings
    formatVersion='0.3'

    publicID = '-//BaderWare//DTD QA Assistant Checklist File ' \
            + formatVersion + '//EN'
    canonicalURL = 'http://qa-assistant.sf.net/dtds/checklist/' \
            + formatVersion + '/checklist.dtd'
    
    # TreeStore entries displayed on the screen
    ISITEM=0     # Entry is an item as opposed to category
    DISPLAY=1    # Write the output to the review
    SUMMARY=2    # Unique title for the entry
    DESC=3       # Long description of what to do to verify the entry
    RESOLUTION=4 # Current resolution
    OUTPUT=5     # Current resolution's output
    RESLIST=6    # Python list of possible resolutions
    OUTPUTLIST=7 # Python hash of outputs keyed to resolution
    TEST=8       # Python class that holds any automated test information

    class __Entry:
        '''Private class.  Holds entry information until ready to output.'''

    class __Property:
        '''Property information.'''

        def __init__(self, type, value):
            '''Initialize a property.
            
            Attributes:
            type -- Type of the property.
            value -- Property value.
            '''
            self.type = type
            self.value = value

    class __Test:
        '''Information related to automated tests embedded in the XML files.
        
        This class is meant to be invoked by the CheckList class.  It will be
        wrapped in CheckList methods `run_test(SUMMARY)` and `run_all_tests()`

        It won't be used directly by other programs because it is assumed that
        getting properties from the CheckList into the Test would be harder.
        If this is not the case, this class may become public and outside code
        may use its interface directly.
        '''
        def run():
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
        self.filename = path
        self.resolution = 'Needs-Reviewing'
        self.functions = []
        self.properties = {}
        self.customItemsIter = None
        self.addPaths = {}
        self.__unspan = re.compile(r'([^<]*)(<span[^>]*>)?([^<]*)(</span>)?(.*)')
        libxml2.registerErrorHandler(self.__no_display_parse_error, None)
        ctxt = libxml2.newParserCtxt()
        try:
            checkFile = ctxt.ctxtReadFile(path, None, libxml2.XML_PARSE_DTDVALID)
        except libxml2.treeError:
            raise error.InvalidChecklist('%s was not an XML file' % (path))

        if ctxt.isValid() == False:
            raise error.InvalidChecklist('File does not validate against ' \
                    'the checklist DTD')

        root = checkFile.getRootElement()
        if root.name != 'checklist':
            raise error.InvalidChecklist('File is not a valid checklist ' \
                    'policy file')
        if root.prop('version') != self.formatVersion:
            raise error.InvalidChecklist('Checklist file is not a known ' \
                    'version')
       
        # Extract the name and revision of the CheckList
        self.name = root.prop('name')
        if not self.name:
            raise error.InvalidChecklist('Checklist file does not specify ' \
                    'a name for itself')
        self.revision = root.prop('revision') or '0'

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
            self.name += ' savefile'
            self.revision = 0
        
        # Extract properties from the CheckList file
        properties = root.xpathEval2('/checklist/properties/property')
        for p in properties:
            self.properties[p.prop('name')] = self.__Property(p.prop('type'), \
                    p.content)

        # Extract functions for the QA menu
        functions = root.xpathEval2('/checklist/functions/function')
        for function in functions:
            self.functions.append(function.content)

        # Record each category as a toplevel in the tree
        categories = root.xpathEval2('/checklist/category')
        self.entries = {}
        for category in categories:
            newCat = self.append(None)
            self.set(newCat,
                    self.ISITEM, False,
                    self.RESLIST, ['Needs-Reviewing', 'Pass', 'Fail'],
                    self.RESOLUTION, 'Needs-Reviewing',
                    self.OUTPUT, None,
                    self.OUTPUTLIST, {'Needs-Reviewing':None,
                                 'Pass':None, 'Fail':None},
                    self.SUMMARY, category.prop('name'),
                    self.TEST, None)
            self.entries[category.prop('name').lower()] = newCat

            # Entries are subheadings
            node = category.children
            while node:
                if node.name == 'description':
                    # Set DESCRIPTION of the heading
                    desc = string.join(string.split(node.content))
                    self.set(newCat, self.DESC, desc)
                elif node.name == 'entry':
                    entry = self.__xml_to_entry(node)
                    entryIter=self.append(newCat)
                    self.set(entryIter,
                            self.ISITEM, True,
                            self.DISPLAY, entry.display,
                            self.SUMMARY, entry.name,
                            self.TEST, entry.test,
                            self.DESC, entry.desc)
                    self.entries[entry.name.lower()] = entryIter
                    
                    # Construct the resolution from multiple states
                    outputList={'Needs-Reviewing': ''}
                    resolutionList=['Needs-Reviewing']
                    for i in range(len(entry.states)):
                        name = entry.states[i]['name']
                        output = self.pangoize_output(name,
                                entry.states[i]['output'])
                        outputList[name] = output
                        if name != 'Needs-Reviewing':
                            resolutionList.append(entry.states[i]['name'])
                        
                    self.set(entryIter,
                            self.RESLIST, resolutionList,
                            self.OUTPUTLIST, outputList,
                            self.RESOLUTION, entry.state,
                            self.OUTPUT, outputList[entry.state])
                else:
                    # DTD validation should make this ignorable.
                    pass
                  
                node = node.next

        checkFile.freeDoc()

    def do_resolution_changed(self, newValue):
        ### FIXME: We need to actually process resolution changed requests
        # here.
        print "This is a test of the resolution changed signal"
        print 'The new value is %s' % newValue
        pass

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
            raise error.DuplicateItem, ('%s is already present in the checklist.' % (self.entries[sumLow]))

        # Set up all the default values.
        if item == None:
            item = True
        if display == None:
            display = True
        resolution = resolution or 'Needs-Reviewing'
        output = output or ''
        desc = desc or None
        resList = resList or ['Needs-Reviewing', 'Pass', 'Fail', 'Non-Blocker', 'Not-Applicable']
        if outputList:
            outputList = outputList
        else:
            for res in resList:
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
                        self.SUMMARY, 'Custom Checklist Items',
                        self.ISITEM, False,
                        self.RESLIST, ['Needs-Reviewing', 'Pass', 'Fail'],
                        self.RESOLUTION, 'Needs-Reviewing',
                        self.OUTPUT, None,
                        self.OUTPUTLIST, {'Needs-Reviewing':None,
                                     'Pass':None, 'Fail':None},
                        self.DESC, "Review items that you have comments on even " \
                              "though they aren't on the standard checklist.",
                        self.TEST, None)
                newItem = self.append(self.customItemsIter)
                self.entries['custom checklist items'] = self.customItemsIter
        
        # Set up the new item
        self.set(newItem,
                self.SUMMARY, summary,
                self.DESC, desc,
                self.ISITEM, item,
                self.DISPLAY, display,
                self.RESOLUTION, resolution,
                self.OUTPUT, output,
                self.RESLIST, resList,
                self.OUTPUTLIST, outputList,
                self.TEST, None)
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
        root.setProp('name', self.name)
        self.revision += 1
        root.setProp('revision', str(self.revision))
        
        # Output base checklist information
        node = root.newTextChild(None, 'base', self.baseFilename)
        node.setProp('name', self.baseName)
        node.setProp('revision', self.baseRevision)
       
        # Output properties we're concerned with
        properties = root.newChild(None, 'properties', None)
        for prop in self.properties.keys():
            node = properties.newTextChild(None, 'property',
                    self.properties[prop].value)
            node.setProp('name', prop)
            node.setProp('type', self.properties[prop].type)

        # Output functions
        functions = root.newChild(None, 'functions', None)
        for func in self.functions:
            node = functions.newTextChild(None, 'function', func)
        
        # Output entries
        self.foreach(self.__create_entry, root)

        # Write the file
        doc.saveFormatFileEnc(filename, 'UTF-8', True)
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
        output = string.replace(output, '&amp;', '&')
        output = string.replace(output, '&lt;', '<')
        output = string.replace(output, '&gt;', '>')

        return output

    def pangoize_output(self, resolution, output):
        '''Colorize the output based on the resolution.
        
        Arguments:
        resolution -- state of review that the output string applies to.
        output -- the output string to colorize.

        Returns: the modified output string.
        '''

        output = string.replace(output, '&', '&amp;')
        output = string.replace(output, '<', '&lt;')
        output = string.replace(output, '>', '&gt;')

        ### FIXME: Get the *Colors from gconf
        failColor = 'red'
        minorColor = 'purple'
        passColor = 'dark green'
        if resolution == 'Fail':
            color = failColor
        elif resolution == 'Non-Blocker' or resolution == 'Needs-Reviewing':
            color = minorColor
        elif resolution == 'Pass':
            color = passColor
        else:
            color = None
        if color:
            output = ('<span foreground="' + color + '">' +
                    output + '</span>')
        return output
  
    def set(self, row, *columnValues):
        '''Override the base set method to specify special actions if the
        column is for RESOLUTION.
        '''
        # Perform a set to the new data
        gtk.TreeStore.set(self, row, *columnValues)

        for listIndex in range(0, len(columnValues), 2):
            if columnValues[listIndex] == RESOLUTION:
                column = columnValues[listIndex]
                newValue = columnValues[listIndex+1]
                # Change the OUTPUT as well
                outputlist = self.get_value(row, OUTPUTLIST)
                out = outputlist[newValue]
                self.set(row, OUTPUT, out)

                ### FIXME: Check GConf2 preferences for auto-display on fail
                # Auto display to review if it's a fail
                if newValue == 'Fail' or newValue == 'Non-Blocker':
                    gtk.TreeStore.set(self, row, self.DISPLAY, True)

                self.check_category_resolution(row, newValue)
        
    def check_category_resolution(self, changedRow, newValue):
        '''Checks a rows category to see if its status should change.
        
        Arguments:
        :changedRow: The entry row that has changed.
        :newValue: The new value of the row.

        This function is a small hack.  It really should be a signal handler
        that gets called when a resolution is changed on the CheckList.
        Unfortunately, `gtk.TreeStore` only supports row-changed, not a
        column-changed signal.  So we are instead calling this function when
        the changed signal occurs on the checkView column looking at
        RESOLUTION.

        ### FIXME: Ways to change this function:

        1) Make it able to resync to the current state of the checklist, not
           just on individual entry changes.

           * When given no value on newValue, we need to walk the values of
             each set, tallying what values we are going to set without a
             newValue to compare to.  This is a simpler operation, but the
             code has no shortcuts whereas the current implementation has
             several.  Don't know if there's a performance gain from the
             simplicity or a loss from the lack of shortcuts.  Need to try it
             out and see.
        '''
        # Load category information to check if it needs updating.
        category = self.iter_parent(changedRow)
        if category:
            # We are checking through all the entries of a single category
            catRes = self.get_value(category, self.RESOLUTION)
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
                            self.RESOLUTION)
                    if nodeRes == 'Fail':
                        return
                    entryIter = self.iter_next(entryIter)
        elif (newValue == 'Pass' or newValue == 'Not-Applicable' or 
                newValue == 'Non-Blocker'):
            # Unless another entry is Fail or Needs-Reviewing, change to Pass
            newValue = 'Pass'
            while entryIter:
                nodeRes = self.get_value(entryIter, self.RESOLUTION)
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
    #
    # Helpers to read a checklist
    #
    
    def __no_display_parse_error(self, ctx, str):
        """Disable Displaying parser errors."""
        pass

    def __xml_to_entry(self, node):
        """Converts an entry node from an XML DOM into a python data structure.

        Keyword -- arguments:
        node -- an entry node to convert.

        Returns: an entry data structure.
        """
        entry=self.__Entry()
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
                entry.states=[]
                while state:
                    if state.name == 'state':
                        entry.states.append({'name' : state.prop('name')})
                        output = string.join(string.split(state.content))
                        entry.states[n]['output'] = output
                        if entry.states[n]['output'].strip() == '':
                            entry.states[n]['output'] = entry.name + ': ' + state.prop('name')
                        n += 1
                    else:
                        # DTD validation should catch things that aren't
                        # supposed to end up here.
                        pass
                    state=state.next
            elif fields.name == 'description':
                desc = string.join(string.split(fields.content))
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
            fields=fields.next

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
        if tree.get_value(entryIter, self.ISITEM):
            # Entry node
            entry = root.lastChild().newChild(None, 'entry', None)
            if tree.get_value(entryIter, self.DISPLAY):
                entry.setProp('display', 'true')
            else:
                entry.setProp('display', 'false')
            entry.setProp('state', tree.get_value(entryIter, self.RESOLUTION))

            # state nodes
            resolutions = tree.get_value(entryIter, self.RESLIST)
            outputs = tree.get_value(entryIter, self.OUTPUTLIST)
            states = entry.newChild(None, 'states', None)
            for res in resolutions:
                content = outputs[res]
                if content:
                    content = self.unpangoize_output(content)
                state = states.newTextChild(None, 'state', content)
                state.setProp('name', res)
                
            # test node
            test = tree.get_value(entryIter, self.TEST)
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
        entry.setProp('name', tree.get_value(entryIter, self.SUMMARY))
        descNode = entry.newTextChild(None, 'description',
                tree.get_value(entryIter, self.DESC))

gobject.signal_new('resolution-changed', CheckList,
        gobject.SIGNAL_RUN_LAST, gobject.TYPE_BOOLEAN,
        (gobject.TYPE_STRING,))
gobject.type_register(CheckList)
