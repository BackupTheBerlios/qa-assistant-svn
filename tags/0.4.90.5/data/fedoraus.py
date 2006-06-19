# File: fedoraus.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 18 April 2005
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
'''
'''
__revision__ = '$Rev$'

import os
import md5
import tempfile
import gzip
import bz2

import rpm
import urlgrabber

from functions import *

class FileError(QAError):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)

class Bzip2File(file):
    '''Minimal Bzip2File interface.

    This gives us an interface to bzip2 decompression similar to GzipFile.
    It only provides decompression in the form of the read() function.
    Initialization must be done by passing an open filehandle through the
    fileobj parameter.

    This gives us just enough to be able t use this with rpm packages whose
    payload has been compressed with bzip2.
    '''
    __READSIZE = 8192
    def __init__(self, filename=None, mode=None, compresslevel=None, fileobj=None):
        self.fileobj = fileobj
        self.decompressor = bz2.BZ2Decompressor()
        self.buffer = None

    def read(self, bufsize=None):
        if self.buffer == -1:
            return ''
        if bufsize == 0:
            return
        if bufsize == None:
            bufsize = -1
        while bufsize < 0 or len(self.buffer) < bufsize:
            compressed = self.fileobj.read(self.__READSIZE)
            if not compressed:
                output = self.buffer
                self.buffer = -1
                return output
            try:
                self.buffer += self.decompressor(compressed)
            except EOFError:
                if self.buffer:
                    output = self.buffer
                    self.buffer = -1
                    return output
        output = self.buffer[0:bufsize]
        self.buffer = self.buffer[bufsize:-1]
        return output
    
    def close(self):
        self.buffer = None
        self.decompressor = bz2.BZ2Decompressor()
        
class QAFunctions(BaseQAFunctions):
    '''

    '''
    
    __BLOCKSIZE = 8192

    def __init__(self, checklist):
        '''
        '''
        self.srpmDir = None
        BaseQAFunctions.__init__(self, checklist)

    #
    # Output functions
    #
    
    def header(self):
        '''Output the header for the review.

        The fedora.us header consists of a Review state: PUBLISH +1
        or NEEDSWORK.  This is followed by a list of the MD5Sums of
        package files involved.
        '''
        # Extract the resolution from the checklist
        if self.checklist.resolution == 'Pass':
            buf = 'APPROVED\n\n'
        elif self.checklist.resolution == 'Fail':
            buf = 'NEEDSWORK\n\n'
        else:
            buf = self.checklist.resolution + '\n\n'
            
        buf += 'MD5Sums:\n'
        buf += self.checklist.properties['SRPMMD5sum'].value
        #for hashSum in self.checklist.properties['fileMD5s'].value:
        #    buf += hashSum
        return buf
    
    def footer(self):
        return ''

    #
    # UI (Menu/toolbar) functions
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
        '''Find the SRPM MD5s from the SRPM filename.

        This may go away as there is already an equivalent method using
        properties to make the setting.  No need for a second menu entry.
        '''
        self.srpm_md5()
        self.srpm_internal_md5s()

    #
    # Properties functions
    #

    def srpm_from_ticket(self):
        '''Retrieve the latest srpmURL from the buzilla URL.
        '''
        try:
            bugzillaURL = self.checklist.properties['ticketURL'].value
        except KeyError:
            # No ticket URL was given, set nothing
            return

        if not bugzillaURL:
            # No ticket URL was given, set nothing
            return

        data = urlgrabber.urlread(bugzillaURL)
        srpmList = re.compile('"((ht|f)tp(s)?://.*?\.src\.rpm)"', re.IGNORECASE).findall(data)
        if srpmList == []:
            # No SRPM was found.  Just decide not to set anything.
            return
        # Set the srpm to the last SRPM listed on the page
        srpmURL = srpmList[-1][0]
        if not srpmURL:
            # No srpm found.  Just decide not to set anything.
            return
        # Download the srpm to the temporary directory.
        urlgrabber.urlgrab(srpmURL, self.tmpDir)
        # Fill the SRPMfile properties with the srpm in the temp directory
        self.checklist.properties['SRPMfile'].value = (
                self.tmpDir + os.path.basename(srpmURL))
        
    def srpm_md5(self):
        '''Get the md5sum of a src.rpm.
        '''
        hasher = md5.new()
        if (self.checklist.properties.has_key('SRPMfile') and
                self.checklist.properties.has_key('SRPMMD5sum') and
                self.checklist.properties['SRPMfile'].value):
            try:
                fileHash = self._hash_file(
                        self.checklist.properties['SRPMfile'].value, hasher)
            except IOError:
                self.checklist.properties['SRPMMD5sum'].value = None
                return
            del hasher
            self.checklist.properties['SRPMMD5sum'] = (
                    fileHash.keys()[0] + ' ' + fileHash.values()[0])

    def srpm_internal_md5s(self):
        '''Create hashes of the files internal to the srpm.
        '''
        if self.checklist.properties.has_key('fileMD5s'):
            try:
                srpmDir = self._expand_srpm()
            except FileError:
                # We were unable to expand the srpm, blank the MD5s and return
                self.checklist.properties['fileMD5s'] = ''
                return
            hasher = md5.new()
            fileHashes = self._hash_directory(srpmDir, hasher)
            del hasher

            output = []
            for files in fileHashes.keys():
                output.append(files + ' ' + fileHashes[files])
            self.checklist.properties['fileMD5s'] = "\n".join(output)

    ### FIXME: Unimplemented tests:
    # check_signatures(): checks that the signatures on an rpm are valid.
    # Needs to check against several keyrings: main rpm db, private fedora db,
    # gpg keyring.
    # check_hashes(): Check the hashes within the rpm against the actual
    # hashes of the files.  A discrepency means someone's been monkeying
    # around with the hashes inside the rpm.

    #
    # Properties helpers
    #

    def _expand_srpm(self):
        # Remove prior expanded SRPMS
        if self.srpmDir:
            self._recursive_rmdir(self.srpmDir)
        # Check that the srpm exists
        if not self.checklist.properties.has_key('SRPMfile'):
            raise FileError('No SRPM file listed')
        
        srpmFile = self.checklist.properties['SRPMfile'].value
        if not os.access(srpmFile, os.F_OK | os.R_OK):
            raise FileError('Unable to read the SRPM file %s' % (srpmFile,))

        # Create a new directory
        self.srpmDir = tempfile.mkdtemp(dir=self.tmpDir)

        # Read the header from the rpm
        transSet = rpm.TransactionSet()
        transSet.setVSFlags(rpm._RPMVSF_NOSIGNATURES | rpm.RPMVSF_NOHDRCHK)
        try:
            srpmHandle = file(srpmFile, 'rb')
        except IOError:
            raise FileError('Unable to read the SRPM file %s' %(srpmFile,))

        try:
            rpmHeader = transSet.hdrFromFdno(srpmHandle.fileno())
        except rpm.error:
            raise FileError('Unable to read an rpm header from %s' %(srpmFile,))
        # The srpm's filehandle is now at the payload

        compressMethod = rpmHeader[rpm.RPMTAG_PAYLOADCOMPRESSOR] or 'gzip'
        if compressMethod == 'gzip':
            payload = gzip.GzipFile(None, 'rb', None, srpmHandle)
        elif compressMethod == 'bzip2':
            payload = Bzip2File(None, 'rb', None, srpmHandle)
        else:
            raise FileError('SRPM uses an unsupported compresor: %s' %
                    (compressMethod,))
        cmd = 'cpio -idum --no-absolute-filenames --force-local --quiet'
        origDir = os.getcwd()
        os.chdir(self.srpmDir)
        cpio = os.popen(cmd, 'w', self.__BLOCKSIZE)
        os.chdir(origDir)
        data = payload.read(self.__BLOCKSIZE)
        while data:
            cpio.write(data)
            data = payload.read(self.__BLOCKSIZE)

        cpio.close()
        payload.close()
        srpmHandle.close()
        return self.srpmDir
        
    def _hash_directory(self, directory, hasher):
        '''Get the cryptogaphic hash of all the files in the directory.

        Attributes:
        directory: The directory to hash the files of.
        hasher: hash object to feed the file to.
        '''
        fileHashes = {}
        directories = []
        for filename in os.listdir(directory):
            srcFile = os.path.join(directory, filename)
            if (os.path.isdir(srcFile)):
                directories.append(filename)
                break
            myHasher = hasher.copy()
            fileHashes.update(self._hash_file(srcFile, myHasher))
            del myHasher

        if len(directories) > 0:
            raise QAError('Unexpected subdirectories', fileHashes)

        return fileHashes

    def _hash_file(self, filename, hasher):
        '''Gets the cryptographic hash of a file.
        
        Attributes:
        filename: filename to hash.
        hasher: hash object to feed the file to.

        This functions returns the hex representation of a hash of a file.
        '''
        fh = file(filename, 'r')
        chunk = fh.read(self.__BLOCKSIZE)
        while chunk:
            hasher.update(chunk)
            chunk = fh.read(self.__BLOCKSIZE)
        fh.close()
        return {os.path.basename(filename) : hasher.hexdigest()}
