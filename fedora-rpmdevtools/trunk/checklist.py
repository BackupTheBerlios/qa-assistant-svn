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

_checklistFileVersion_='0.1'

# TreeStore entries displayed on the screen
ISITEM=0
DISPLAY=1
SUMMARY=2
DESC=3
INPUT=4
RESOLUTION=5
OUTPUT=6
RESLIST=7
OUTPUTLIST=8

class Error(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

class CheckList:
    """Holds the data associated with the checklist.
    
    Data is held in a gtk TreeModel.  Saving the state of the checklist
    should consist of saving the data in the TreeModel along with a reference
    to the checklist we're operating upon.
    """

    class __Entry:
        """Private class.  Holds entry information until ready to output."""

    def __init__(self, path):
        
        checkFile = libxml2.parseFile(path)
        ### FIXME: validate
        root = checkFile.children
        if root.name != 'checklist':
            raise CheckListError("File is not a valid checklist policy file")
        if root.prop('version') != _checklistFileVersion_:
            raise CheckListError("Checklist file is not a known version")
        
        # Extract the type from the checklist tag
        self.type = root.prop('name')
        if not self.type:
            raise CheckListError("Checklist file does not specify a type in the name attribute")
        self.revision = root.prop('revision')
        if not self.revision:
            self.revision='0'

        # Store the checklist into a GtkTreeModel
        self.tree = gtk.TreeStore(gobject.TYPE_BOOLEAN,
                                  gobject.TYPE_BOOLEAN,
                                  gobject.TYPE_STRING,
                                  gobject.TYPE_STRING,
                                  gobject.TYPE_STRING,
                                  gobject.TYPE_STRING,
                                  gobject.TYPE_STRING,
                                  gobject.TYPE_PYOBJECT,
                                  gobject.TYPE_PYOBJECT)

        # Record each category as a toplevel in the tree
        categories = root.xpathEval2('/checklist/category')
        for category in categories:
            iter = self.tree.append(None)
            self.tree.set(iter,
                          ISITEM, False,
                          RESLIST, ['Needs-Reviewing', 'Pass', 'Fail'],
                          RESOLUTION, 'Needs-Reviewing',
                          OUTPUT, None,
                          OUTPUTLIST, {'Needs-Reviewing':None, 
                                       'Pass':None, 'Fail':None},
                          SUMMARY, category.prop('name'))

            # Entries are subheadings
            node = category.children
            while node:
                if node.name == 'description':
                    # Set DESCRIPTION of the heading
                    self.tree.set(iter, DESC, node.content)
                elif node.name == 'entry':
                    entry = self.__xmlToEntry(node)
                    entryIter=self.tree.append(iter)
                    self.tree.set(entryIter,
                                  ISITEM, True,
                                  DISPLAY, entry.display,
                                  SUMMARY, entry.name,
                                  DESC, entry.desc,
                                  INPUT, entry.input)
                    # Construct the resolution from multiple states
                    resolutions={'Needs-Reviewing': None}
                    resolutionList=['Needs-Reviewing']
                    for i in range(len(entry.states)):
                        name = entry.states[i]['name']
                        resolutions[name] = entry.states[i]['output']
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

    def __xmlToEntry(self, node):
        """Converts an entry node from an XML DOM into a python data structure.

        Keyword -- arguments:
        node -- an entry node to convert.

        Returns: an entry data structure.
        """
        entry=self.__Entry()
        # Set defaults
        entry.display = False
        entry.input = None

        entry.name = node.prop('name')
        fields = node.children
        while fields:
            if fields.name == 'display':
                if string.lower(fields.prop('default')) == 'true':
                    entry.display = True
                else:
                    entry.display = False
            if fields.name == 'states':
                state = fields.children
                n=0
                entry.states=[]
                while state:
                    if state.name == 'state':
                        entry.states.append({'name' : state.prop('name')})
                        output = state.children
                        while output:
                            if output.name == 'output':
                                entry.states[n]['output']=output.content
                            output=output.next
                        if not entry.states[n].has_key('output'):
                            entry.states[n]['output'] = entry.name + ': ' + state.prop('name')
                        n+=1
                    else:
                        # DTD validation should catch things that aren't
                        # supposed to end up here.
                        pass
                    state=state.next
            elif fields.name == 'description':
                entry.desc = fields.content
            elif fields.name == 'input':
                entry.input = fields.content
            else:
                # DTD validation should prevent anything uwated from
                # ending up here.
                pass
            fields=fields.next

        return entry
