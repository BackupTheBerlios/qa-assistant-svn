# File: savefile.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 29 April, 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
"""
"""
__revision__ = "$Rev$"

import os, re
import libxml2
import checklist

class SaveFile:
    ''' '''

    def __init__(self, tree, properties, dtd, filename='None'):
        ''' '''
        self.tree = tree
        self.properties = properties
        self.dtd = dtd
        self.filename = filename

    #
    # Public Methods
    #
    def publish(self):
        '''Saves the current state of the checklist into a savefile.
        
        The information to create the savefile is already stored in the
        SaveFile object.  The important pieces are self.filename which was
        set by a call to set_filename(), self.properties, and self.tree (set
        by the initial creation of the SaveFile object.)
        '''
        
        # Create the xml DOM conforming to qasave.dtd
        dtd = libxml2.parseDTD(None, self.dtd)
        dtd.name = 'qasave'
        doc = libxml2.newDoc('1.0')
        ### FIXME: Lookup the difference between an internal and external
        # subset
        doc.intSubset = dtd
        ### FIXME: Have to figure out how to output a call to a DTD reference,
        # but not the DTD itself.
        # doc.addChild(dtd)
        
        # Output root node
        root = doc.newChild(None, 'qasave', None)
        root.setProp('version', '0.1')
        
        # Output checklist
        node = root.newChild(None, 'checklist', None)
        node.setProp('name', self.properties.checklistName)
        node.setProp('revision', self.properties.checklistRev)
        node.addContent(self.properties.checklist)
       
        # Output properties we're concerned with
        properties = root.newChild(None, 'properties', None)
        if self.properties.bugzillaURL:
            properties.addChild(self.__create_property('bugzillaURL',
                self.properties.bugzillaURL))
        if self.properties.bugzillaNumber:
            properties.addChild(self.__create_property('bugzillaNumber',
                self.properties.bugzillaNumber))
        if self.properties.SRPM:
            properties.addChild(self.__create_property('SRPM',
                self.properties.SRPM.filename))
     
        # Output entries
        self.tree.foreach(self.__create_entry, root)

        # Write the file
        doc.saveFormatFileEnc(self.filename, 'UTF-8', True)

    def load(self):
        ''' '''
        # Load the filename into an xml DOM
        # Create a checklist object from the checklist named in the File
        # Apply changes from the filename into the checklit tree
        # Return the checklist

        pass

    def set_filename(self, filename):
        '''Updates the filename to be used.'''
        
        self.filename = filename

    #
    # Helper methods
    #
    def __create_property(self, propName, value):
        '''Creates a property xml node for output '''

        node = libxml2.newNode('property')
        node.setProp('name', propName)
        node.addContent(value)
        return node
    
    def __create_entry(self, tree, path, iter, root):
        '''Create an entry node and add it to the document.'''

        if tree.get_value(iter, checklist.MODIFIED):
            entry = root.newChild(None, 'entry', None)
            entry.setProp('name', tree.get_value(iter, checklist.SUMMARY))
            if tree.get_value(iter, checklist.DISPLAY) == False:
                display = 'false'
            else:
                display = 'true'
            entry.setProp('display', display)
            entry.setProp('state', tree.get_value(iter, checklist.RESOLUTION))
            resolutions = tree.get_value(iter, checklist.RESLIST)
            if resolutions:
                outputs = tree.get_value(iter, checklist.OUTPUTLIST)
                unspan = re.compile(r'([^<]*)(<span[^>]*>)?([^<]*)(</span>)?(.*)')
                states = entry.newChild(None, 'states', None)
            for res in resolutions:
                content = outputs[res]
                if content:
                    content = unspan.match(content).expand(r'\g<1>\g<3>\g<5>')
                state = states.newChild(None, 'state', None)
                state.setProp('name', res)
                state.addContent(content)
