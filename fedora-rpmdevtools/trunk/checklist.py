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

### Work on this: need to have an entry for each field and subfield of an
# entry.  Not all of these items will be displayed.  Some will be meta data
# in the checklist tree and be spit out to the editor window/finished review.
DISPLAY=0
RESOLUTION=1
SUMMARY=2
DESC=3
OUTPUT=4

class Error(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

class CheckList:
    """Holds the data associated with the checklist"""

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
                                       gobject.TYPE_STRING,
                                       gobject.TYPE_STRING,
                                       gobject.TYPE_STRING,
                                       gobject.TYPE_STRING)
        categories = root.xpathEval2('/checklist/category')
        # Record each category as a toplevel in the tree
        for category in categories:
            iter = self.tree.append(None)
            self.tree.set(iter, DISPLAY, None,
                    RESOLUTION, ' \npass\nfail',
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
                    ### FIXME: Not the complete entry.
                    self.tree.set(entryIter, DISPLAY, entry.display,
                            RESOLUTION, entry.states[0], ### FIXME
                            SUMMARY, entry.name,
                            DESC, entry.desc,
                            OUTPUT, entry.states[0]['output']);
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
