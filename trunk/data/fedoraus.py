# File: fedoraus.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 18 April 2005
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
'''
'''
__revision__ = '$Rev$'

from functions import *

class QAFunctions(BaseQAFunctions):
    '''

    '''
        
    #
    # Output functions
    #
    
    def header(self):
        '''Output the header for the revew.

        The fedora.us header consists of a Review state: PUBLISH +1
        or NEEDSWORK.  This is followed by a list of the MD5Sums of
        package files involved.
        '''
        # Extract the resolution from the checklist
        if self.checklist.resolution == 'Pass':
            buf = 'PUBLISH +1\n\n'
        elif self.checklist.resolution == 'Fail':
            buf = 'NEEDSWORK\n\n'
        else:
            buf = self.checklist.resolution + '\n\n'
            
        buf += 'MD5Sums:\n'
        #buf += self.checklist.properties['SRPMMD5sum'].value
        #for hashSum in self.checklist.properties['fileMD5s'].value:
        #    buf += hashSum
        return buf
    
    def footer(self):
        return ''

    #
    # UI (Menu/tolbar) functions
    #
    
    def get_ui(self, app):
        uiDef = BaseQAFunctions.get_ui(self, app)
        uiElements = '''<ui>
            <menubar name="MainMenu">
              <menu action="QAActions">
                <menuitem action="FromSRPM" position="top"/>
                <separator/>
              </menu>
            </menubar>
          </ui>
          '''
        uiActions = (('FromSRPM', None, 'Start from _SRPM', None,
            'Load the properties for this review from an SRPM',
            self.from_srpm_cb),)
        actiongroup = gtk.ActionGroup('QA Menu')
        actiongroup.add_actions(uiActions, app)
        uiDef.append((actiongroup, uiElements))
        return uiDef

    def from_srpm_cb(self, action, app, *extras):
        pass

    #
    # Properties functions
    #

    def srpm_from_ticket(self):
        '''Retrieve the latest srpmURL from the buzilla URL.
        '''
        bugzillaURL = self.checklist.properties['ticketURL']
        data = urlgrabber.urlread(bugzillaURL)
        srpmList = re.compile('"((ht|f)tp(s)?://.*?\.src\.rpm)"', re.IGNORECASE).findall(data)
        if srpmList == []:
            # No SRPM was found.  Just decide not to set anything.
            return
        srpmURL = srpmList[-1][0]
        if not srpmURL:
            # No srpm found.  Just decide not to set anything.
            return
        self.checklist.properties['SRPMfile'] = srpmURL
        
    def srpm_md5(self):
        '''Get the md5sum of a src.rpm.
        '''
        pass
    def srpm_internal_md5s(self):
        pass

    def srpm_from_ticket(self):
        pass
        '''
    <property name="SRPMfile" type="file">
    <property name="SRPMMD5sum" type="md5sum">
    <property name="fileMD5s" type="string">
        '''
