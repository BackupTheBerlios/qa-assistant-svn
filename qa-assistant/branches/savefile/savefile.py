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
import checklist, gnomeglade

_qaSaveFileVersion_ = '0.1'

class SaveFile:
    '''A savefile object.

    When we rewrite things, this needs to be merged into the checklist.
    A savefile is a checkpoint in time of the base checklist.
    '''

    class __Entry:
        '''Private class.  Holds entry information until the checklist data
        structure is ready to hold it.
        '''

    publicID = '-//BadgerWare//DTD QA Assistant Save File ' + _qaSaveFileVersion_ + '//EN'
    canonicalURL = 'http://qa-assistant.sf.net/qasave/' + _qaSaveFileVersion_ + '/qasave.dtd'
    def __init__(self, checklist, properties, dtd, filename=None):
        ''' '''
        self.checklist = checklist
        self.properties = properties
        ### FIXME: Instead of using a DTD path, we should be using a DTD
        # PUBLIC identifier and canonical URL.  Need to figure out that
        # piece of technology.
        self.dtd = dtd
        self.filename = filename

    #
    # Public Methods
    #
    def publish(self):
        '''Saves the current state of the checklist into a savefile.
        
        The information to create the savefile is already stored in the
        SaveFile object.  The important pieces are self.filename which was
        set by a call to set_filename(), self.properties, and self.checklist
        (set by the initial creation of the SaveFile object.)
        '''
        
        # Create the xml DOM conforming to qasave.dtd
        dtd = libxml2.parseDTD(None, self.dtd)
        dtd.name = 'qasave'
        doc = libxml2.newDoc('1.0')
        doc.createIntSubset('qasave', self.publicID, self.canonicalURL)
        
        # Output root node
        root = doc.newChild(None, 'qasave', None)
        root.setProp('version', '0.1')
        
        # Output checklist
        node = root.newChild(None, 'checklist', None)
        node.setProp('name', self.checklist.name)
        node.setProp('revision', self.checklist.revision)
        ### FIXME: checklist should know which filename it comes from,
        # instead of properties.
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
        entries = root.newChild(None, 'entries', None)
        self.checklist.tree.foreach(self.__create_entry, entries)

        # Write the file
        doc.saveFormatFileEnc(self.filename, 'UTF-8', True)

        doc.freeDoc()

    def load(self):
        ''' '''

        # Parse the xml into a DOM
        libxml2.registerErrorHandler(self.__no_display_parse_error, None)
        ctxt = libxml2.newParserCtxt()
        saveFile = ctxt.ctxtReadFile(self.filename, None, libxml2.XML_PARSE_DTDVALID)
        if ctxt.isValid() == False:
            ### FIXME create something less generic
            raise Exception('Save file does not validate against the qasave DTD.')

        root = saveFile.getRootElement()
        if root.name != 'qasave':
            ### FIXME create something less generic
            raise Exception('File us not a valid qa save file.')
        if root.prop('version') != _qaSaveFileVersion_:
            ### FIXME create something less generic
            raise Exception('Save file is of a different version than I understand.')
        # Load the appropriate base checklist.
        saveCheck = root.xpathEval2('/qasave/checklist')
        filename = saveCheck[0].content
        filename = os.path.join('data', filename)
        checkFile = gnomeglade.uninstalled_file(filename)
        if not checkFile:
            filename = os.path.join(__programName__, filename)
            checkFile = gnomeglade.locate_file(filename)
        if not checkFile:
            ### FIXME: Throw an exception to get out gracefully
            sys.exit(1)
        newList = checklist.CheckList(checkFile, self.properties)

        # Check that the checklist is the appropriate version
        if (newList.name != saveCheck[0].prop('name')):
            ### FIXME: Throw an exception to get out gracefully
            sys.exit(1)
        if (newList.revision != saveCheck[0].prop('revision')):
            ### FIXME: Think about this some more.
            # I think we just want to pop up a warning dialog and then
            # continue.
            # If the new checklist revision has more entries it will still
            # overlay fine.  But the user may need to look back over completed
            # sections for new entries.
            # If the new revision has less entries, old modified entries will
            # go into the Custom Entries area.
            pass
       
        del saveCheck
        
        saveProperties = root.xpathEval2('/qasave/properties/property')
        for property in saveProperties:
            ### FIXME: Properties needs to supply a set interface that
            # discards illegal values.

            # Set properties through the interface.
            try:
                self.properties.set(property.prop('name'), property.content)
            except AttributeError, id:
                if id == 1:
                    # save property.prop(name) and .content into a hash.
                    # When we are done with the loop, check the hash.
                    # If there are values in it, popup a warning dialog
                    # that the save file had invalid entries that will be
                    # discarded.
                    pass
            except:
                ### FIXME: I haven't written the properties interface yet so
                # this is going to generate an exception.  I think the future
                # is to merge both properties and savefile into checklist so
                # this is going to disappear.
                pass
        del saveProperties
        
        saveEntries = root.xpathEval2('/qasave/entries/entry')
        for node in saveEntries:
            entry = self.__xml_to_entry(node, newList)
            iter = newList.entries[entry.name]
            if not iter:
                #   Create the Custom Entries area and get an iter referencing a
                #   new value there.  Add entry.prop('name') into the iter.
                #   Add None for checklist.DESC
                pass
            newList.tree.set(iter, checklist.ISITEM, True,
                    checklist.DISPLAY, entry.display,
                    checklist.MODIFIED, True,
                    checklist.SUMMARY, entry.name,
                    checklist.RESOLUTION, entry.res,
                    checklist.OUTPUT, entry.out,
                    checklist.RESLIST, entry.reslist,
                    checklist.OUTPUTLIST, entry.outlist
                    )
            
        del saveEntries

        saveFile.freeDoc()

        return newList 

    def set_filename(self, filename):
        '''Updates the filename to be used.'''
        
        self.filename = filename

    #
    # Helper methods
    #
    def __xml_to_entry(self, node, newList):
        '''Reformats an XML node into an entry structure.'''
        ### FIXME: When we combine with checklist, we won't need to pass
        # newList in any longer.
        entry = self.__Entry()
        entry.name = node.prop('name')
        if node.prop('display') == 'true':
            entry.display = True
        else:
            entry.display = False
            
        states = node.children
        while states.name != 'states':
            states = states.next
        state = states.children

        entry.res = node.prop('state')
        entry.reslist = []
        entry.outlist = []
        while state:
            if state.name == 'state':
                entry.reslist.append(state.prop('name'))
                entry.outlist.append(newList.colorize_output(
                    state.prop('name'), state.content))
                if state.prop('name') == entry.res:
                    entry.out = entry.outlist[-1]
            state = state.next

        return entry

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

    def __no_display_parse_error(self, ctx, str):
        """Disable Displaying parser errors."""
        pass
