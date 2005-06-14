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
    '''
    <function type="header">srpm_header</function>
    <function type="user">from_srpm</function>
    <function type="user">from_ticket</function>
    <function type="user">separator</function>
    <function type="user">add_item</function>
    <function type="user">separator</function>
    <function type="user">publish</function>
    <function type="user">submit_ticket</function>
    '''

class QAFunctionsMenu(BaseQAFunctionsMenu):
    '''

    '''
    def __init__(self, functions):
        BaseQAFunctionsMenu.__init__(self)
        self.add('')
        
