# File: checklist.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 04 Mar 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Description: Class file to load a description of a checklist into internal
# structures.
# Id: $Id$
"""Class file to load a description of a checklist into internal structures.
"""

import libxml2, string
import gtk, gobject

_checklistFileVersion_='0.2'

# TreeStore entries displayed on the screen
ISITEM=0     # Entry is an item as opposed to category
DISPLAY=1    # Write the output to the review
MODIFIED=2   # Boolean holding whether the value has been modified
SUMMARY=3    # Unique title for the entry
DESC=4       # Long description of what to do to verify the entry
RESOLUTION=5 # Current resolution
OUTPUT=6     # Current resolution's output
RESLIST=7    # Python list of possible resolutions
OUTPUTLIST=8 # Python hash of outputs keyed to resolution

class Error(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

class duplicateItemError(Error):
    pass

class CheckList:
    """Holds the data associated with the checklist.
    
    Data is held in a gtk TreeModel.  Saving the state of the checklist
    should consist of saving the data in the TreeModel along with a reference
    to the checklist we're operating upon.
    """

    class __Entry:
        """Private class.  Holds entry information until ready to output."""

    def __init__(self, path, props):

        self.customItemsPath = None
        self.props = props
        self.addPaths = {}
        libxml2.registerErrorHandler(self.__no_display_parse_error, None)
        ctxt = libxml2.newParserCtxt()
        checkFile = ctxt.ctxtReadFile(path, None, libxml2.XML_PARSE_DTDVALID)

        if ctxt.isValid() == False:
            raise Error("File does not validate against the checklist DTD")

        root = checkFile.getRootElement()
        if root.name != 'checklist':
            raise Error("File is not a valid checklist policy file")
        if root.prop('version') != _checklistFileVersion_:
            raise Error("Checklist file is not a known version")
        
        # Extract the type from the checklist tag
        self.name = root.prop('name')
        if not self.name:
            raise Error("Checklist file does not specify a name for itself")
        self.revision = root.prop('revision')
        if not self.revision:
            self.revision='0'
        self.type = root.prop('type')
        if not self.type:
            self.type = 'generic'

        # Store the checklist into a GtkTreeModel
        self.tree = gtk.TreeStore(gobject.TYPE_BOOLEAN,
                                  gobject.TYPE_BOOLEAN,
                                  gobject.TYPE_BOOLEAN,
                                  gobject.TYPE_STRING,
                                  gobject.TYPE_STRING,
                                  gobject.TYPE_STRING,
                                  gobject.TYPE_STRING,
                                  gobject.TYPE_PYOBJECT,
                                  gobject.TYPE_PYOBJECT)

        # Record each category as a toplevel in the tree
        categories = root.xpathEval2('/checklist/category')
        self.entries = {}
        for category in categories:
            iter = self.tree.append(None)
            self.tree.set(iter,
                          ISITEM, False,
                          MODIFIED, False,
                          RESLIST, ['Needs-Reviewing', 'Pass', 'Fail'],
                          RESOLUTION, 'Needs-Reviewing',
                          OUTPUT, None,
                          OUTPUTLIST, {'Needs-Reviewing':None,
                                       'Pass':None, 'Fail':None},
                          SUMMARY, category.prop('name'))
            self.entries[category.prop('name')] = iter

            # Entries are subheadings
            node = category.children
            while node:
                if node.name == 'description':
                    # Set DESCRIPTION of the heading
                    desc = string.join(string.split(node.content))
                    self.tree.set(iter, DESC, desc)
                elif node.name == 'entry':
                    entry = self.__xml_to_entry(node)
                    entryIter=self.tree.append(iter)
                    self.tree.set(entryIter,
                                  ISITEM, True,
                                  MODIFIED, False,
                                  DISPLAY, entry.display,
                                  SUMMARY, entry.name,
                                  DESC, entry.desc)
                    self.entries[entry.name] = entryIter
                    
                    # Construct the resolution from multiple states
                    resolutions={'Needs-Reviewing': None}
                    resolutionList=['Needs-Reviewing']
                    for i in range(len(entry.states)):
                        name = entry.states[i]['name']
                        output = self.colorize_output(name,
                                entry.states[i]['output'])
                        resolutions[name] = output
                        if name != 'Needs-Reviewing':
                            resolutionList.append(entry.states[i]['name'])
                        
                    self.tree.set(entryIter,
                                  RESLIST, resolutionList,
                                  OUTPUTLIST, resolutions,
                                  RESOLUTION, 'Needs-Reviewing',
                                  OUTPUT, resolutions['Needs-Reviewing'])
                else:
                    # DTD validation should make this ignorable.
                    pass
                  
                node = node.next

        checkFile.freeDoc()
        # More efficient to do the stuff in the signal handlers manually
        # during setup and only register them afterwards.
        self.tree.connect('row-inserted', self.__added_row)
        self.tree.connect('row-changed', self.__modified_row)

    def add_entry(self, summary, item=None, display=None,
            desc=None, resolution=None, output=None,
            resList=None, outputList=None):
        '''Adds new items to the checklist.
        
        Arguments:
        summary -- Summary of problem (also its key.)
        
        Keyword arguments:
        item -- entry is an item rather than a category. (default True)
        display -- display the entry in output review. (default True)
        desc -- long description about how to determine if the item
                item has passed or failed. (default None)
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
        if self.entries.has_key(summary):
            raise duplicateItemError, ('%s is already present in the checklist.' % (self.entries[summary]))

        # Set up all the default values.
        if item == None:
            item = True
        if display == None:
            display = True
        resolution = resolution or 'Needs-Reviewing'
        output = output or None
        desc = desc or None
        resList = resList or ['Needs-Reviewing', 'Pass', 'Fail', 'Non-Blocker', 'Not-Applicable']
        if outputList:
            outputList = outputList
        else:
            for res in resList:
                outputList[res] = None
            outputList[resolution] = output
       
        if self.customItemsPath:
            iter = self.tree.get_iter(self.customItemsPath)
            newItem = self.tree.append(iter)
        else:
            iter = self.tree.append(None)
            if summary == 'Custom Checklist Items':
                self.customItemsPath = self.tree.get_path(iter)
                newItem = iter
            else:
                # Create the 'Custom Checklist Items' category
                self.tree.set(iter,
                    SUMMARY, 'Custom Checklist Items',
                    MODIFIED, True,
                    ISITEM, False,
                    RESLIST, ['Needs-Reviewing', 'Pass', 'Fail'],
                    RESOLUTION, 'Needs-Reviewing',
                    OUTPUT, None,
                    OUTPUTLIST, {'Needs-Reviewing':None,
                                           'Pass':None, 'Fail':None},
                    DESC, '''Review items that you have comments on even though they aren't on the standard checklist.''')
                self.customItemsPath = self.tree.get_path(iter)
                newItem = self.tree.append(iter)
        
        # Set up the new item
        self.tree.set(newItem,
                SUMMARY, summary,
                DESC, desc,
                ISITEM, item,
                DISPLAY, display,
                MODIFIED, True,
                RESOLUTION, resolution,
                OUTPUT, output,
                RESLIST, resList,
                OUTPUTLIST, outputList)
        return newItem
        
    def colorize_output(self, resolution, output):
        """Colorize the output based on the resolution.
        
        Arguments:
        resolution -- state of review that the output string applies to.
        output -- the output string to colorize.
        """
        ### FIXME:
        # escaping really goes one level up but there are currently several
        # external functions that call colorize output.  In the future we need
        # to create a function one level up to change output strings and make
        # colorize_output a private method.
        output = string.replace(output, '&', '&amp;')
        output = string.replace(output, '<', '&lt;')
        output = string.replace(output, '>', '&gt;')
        if resolution == 'Fail':
            color = self.props.failColor
        elif resolution == 'Non-Blocker' or resolution == 'Needs-Reviewing':
            color = self.props.minorColor
        elif resolution == 'Pass':
            color = self.props.passColor
        else:
            color = None
        if color:
            output = ('<span foreground="' + color + '">' +
                    output + '</span>')
        return output

    def __modified_row(self, tree, path, iter):
        """Maintain internal values whenever a row is modified.

        The tree needs to set the modified flag on changed rows so that they
        are saved properly.
        """

        if not tree.get_value(iter, MODIFIED):
            tree.set(iter, MODIFIED, True)
        if self.addPaths.has_key(path) and tree.get_value(iter, SUMMARY):
            name = tree.get_value(iter, SUMMARY)
            self.entries[name] = iter
            del self.addPaths[path]
            

    def __added_row(self, tree, path, iter):
        """Maintain some internal values whenever a row is added.
      
        The tree needs to set the modified value on new entries so they get
        saved properly.  We also need to list the path to the item as needing
        to be entered into  self.entries when the summary value becomes
        available.  self.entries allows fast checking for the existence of
        an entry.
        """

        # Set the MODIFIED flag
        tree.set(iter, MODIFIED, True)

        # List the path as needing to be entered into our lookup hash.
        self.addPaths[tree.get_path(iter)] = True

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

        entry.name = node.prop('name')
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
                        n+=1
                    else:
                        # DTD validation should catch things that aren't
                        # supposed to end up here.
                        pass
                    state=state.next
            elif fields.name == 'description':
                desc = string.join(string.split(fields.content))
                entry.desc = desc
            else:
                # DTD validation should prevent anything uwated from
                # ending up here.
                pass
            fields=fields.next

        return entry
