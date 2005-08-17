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

    def get_ui(self):
        uiDef = BaseQAFunctions.get_ui(self)
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
        uiDef.append((uiElements, uiActions))
        return uiDef

    def from_srpm_cb(self, action, extras):
        pass
