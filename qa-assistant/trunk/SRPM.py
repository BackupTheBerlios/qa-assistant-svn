# File: SRPM.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 27 March 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
"""A representation of an SRPM.
"""
__revision__ = "$Rev$"

import rpm
import os, sys, stat
import md5
import gzip, tempfile

__PYVER = int(float(sys.version[:3])*100)
if __PYVER >= 230:
    __HAS_BZ2 = True
    import bz2

class Error(Exception):
    """Base class for SRPM exceptions.
    
    Attributes:
        message -- explanation of the exception.
    """
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)

class FileError(Error):
    """Exception raised when there's problems reading the SRPM file."""
    def __init__(self, message):
        Error.__init__(self, message)

class SecurityError(Error):
    def __init__(self, message, filename):
        Error.__init__(self, message)
        self.filename = filename

class SRPM:
    __PYVER = int(float(sys.version[:3])*100)
    __BLOCKSIZE=8192

    def __init__(self, SRPMFile):
        self.filename=os.path.abspath(SRPMFile)
        if os.access(self.filename, os.F_OK | os.R_OK) == False:
            raise FileError("Unable to read SRPM file %s" % (self.filename))
        self.expanded = False
        self.expandDir = None
        
        transSet = rpm.TransactionSet()
        transSet.setVSFlags(~(rpm._RPMVSF_NOSIGNATURES |
                            rpm._RPMVSF_NODIGESTS | rpm.RPMVSF_NOHDRCHK))
        filehandle = file(self.filename, 'rb')
        self.hdr = transSet.hdrFromFdno(filehandle.fileno())
        self.payloadOffset = filehandle.tell()
        filehandle.close()
        del transSet

        self.compressMethod = self.hdr[rpm.RPMTAG_PAYLOADCOMPRESSOR] or 'gzip'
        self.NVR = (self.hdr[rpm.RPMTAG_NAME] + '-' + 
                self.hdr[rpm.RPMTAG_VERSION] + '-' +
                self.hdr[rpm.RPMTAG_RELEASE])
        self.__calc_hashes()

    def hashes(self):
        """Returns the MD5 hashes of the files in the SRPM."""
        return self.srpmHash, self.fileHashes

    def expand(self, rootDir=None):
        """Moves the files from the RPM Payload into a directory

        """
        ### FIXME: Two problems with current code:
        # 1) Crash in __hash_directories when someone attempts to hash the
        #    a modified directory structure that has directories in it.
        #    (Solution: Use os.path.walk)
        # 2) What should we do in expand when the directory in the way has
        #    extra files in it?  Probably should ask the user....
        if rootDir == None:
            ### FIXME: get directory from GConf2
            rootDir = '/var/tmp'
        directory = os.path.join(rootDir, self.NVR)

        # Check for previous unarchival of rpm file
        if os.path.exists(directory) == False:
            try:
                os.mkdir(directory)
            except:
                raise FileError("Unable to create directory %s" % (directory))
            os.chmod(directory, stat.S_IRWXU)
            if os.listdir(directory):
                raise SecurityError("Somebody changed %s right after we created it." % (directory), directory)
            self.__unarchive(directory)
        elif os.path.isdir(directory) == True:
            # Check ownership of the directory in the way
            os.path.walk(directory, self.__check_ownership, None)
            # Create a temporary directory
            if SRPM.__PYVER >= 230:
                tempDir = mkdtemp(None, None, rootDir)
            else:
                tempfile.tempdir = rootDir
                tempDir = tempfile.mktemp()
                os.mkdir(tempDir)
                os.chmod(tempDir, stat.S_IRWXU)
                if os.listdir(tempDir):
                    raise SecurityError("Somebody changed %s right after we created it." % (tempDir), tempDir)

            # Unarchive our rpm to the tempDir
            self.__unarchive(tempDir)
            hasher = md5.new()
            oldHashes = self.__hash_directory(directory, hasher)
            pristineHashes = self.__hash_directory(tempDir, hasher)
            try:
                self.__check_hashes(oldHashes, pristineHashes)
            except SecurityError:
                # Change this to a FileError because we called it with two
                # directories that we didn't expect would be the same.
                os.path.walk(tempDir, self.__recursive_rm_dir, None)
                raise FileError("%s which has modified files is in the way of running the program again" % (directory))
            else:
                os.path.walk(tempDir, self.__recursive_rm_dir, None)
        else:
            raise FileError("There's a file in the way of our unarchiving to directory %s" % (directory))

        self.expandDir = directory
        self.expanded = True

    def __unarchive(self, directory):
        """Convert an rpm into a directory."""

        filehandle = file(self.filename)
        filehandle.seek(self.payloadOffset)
        if self.compressMethod == 'gzip':
            fd = gzip.GzipFile(None, 'rb', None, filehandle)
        elif self.compressMethod == 'bzip2':
            if (__HAS_BZ2):
                pass
                ### FIXME: This is broken.  Need to check out the bz2 interface
                # in python2.3
                #fd = bz2.BZ2File(None, 'rb', None, filehandle)
            else:
                raise FileError("We don't support payload compressor %s" % (compressMethod))
        else:
            raise FileError("Unknown payload compressor %s" % (compressMethod))
        cmd = 'cpio -idum --no-absolute-filenames --force-local --quiet'
        origDir = os.getcwd()
        os.chdir(directory)
        cpio = os.popen(cmd, 'w', self.__BLOCKSIZE)
        os.chdir(origDir)
        buffer = fd.read(self.__BLOCKSIZE)
        while buffer:
            cpio.write(buffer)
            buffer = fd.read(self.__BLOCKSIZE)
        cpio.close()
        fd.close()
        filehandle.close()

    def __recursive_rm_dir(self, arg, dirname, files):
        for name in files:
            name = os.path.join(dirname, name)
            if os.path.isfile(name) or os.path.islink(name):
                os.unlink(name)
        os.removedirs(dirname)

    def __check_ownership(self, arg, dirname, files):
        uid = os.getuid()
        stats = os.lstat(dirname)
        if stats.st_uid != uid:
            raise FileError("Directory %s has files owned by someone else, so we can't unarchive the rpm" % (dirname))
        for file in files:
            stats = os.lstat(os.path.join(dirname, file))
            if stats.st_uid != uid:
                raise FileError("Directory %s has files owned by someone else, so we can't unarchive the rpm" % (dirname))

    def __check_hashes(self, fileHashes, md5s):
        """Compare two sets of hashes to see if they match.

        If the hashes do not match, a SecurityError is raised.
        """
        for filename in fileHashes.keys():
            if SRPM.__PYVER >= 230:
                rHash = md5s.pop(filename, None)
            else:
                rHash = md5s.get(filename, None)
            if (rHash == None):
                raise SecurityError("%s is in the archive but not listed in the rpm headers" % (filename), filename)
            if rHash != fileHashes[filename]:
                raise SecurityError("MD5 hash in the headers does not match actual hash for %s" % (filename), filename)
            if SRPM.__PYVER < 230:
                del md5s[filename]

        if len(md5s) > 0:
            filenames = []
            for noFile in md5s:
                filenames.append(noFile)
            raise SecurityError("Files listed in the rpm headers do not exist in the archive", filenames)

    def __calc_hashes(self, hashType = None):
        if not hashType:
            hashType = 'md5'
        if not self.expanded:
            self.expand()
        hasher = md5.new()
        self.srpmHash = self.__hash_file(self.filename, hasher)
        del hasher

        hasher = md5.new()
        self.fileHashes = self.__hash_directory(self.expandDir, hasher)
        del hasher

        # Check the MD5s against those saved in the RPM header
        filenames = self.hdr[rpm.RPMTAG_FILENAMES]
        rawMD5s = self.hdr[rpm.RPMTAG_FILEMD5S]
        md5s={}
        for i in range(len(filenames)):
            md5s.update({filenames[i] : rawMD5s[i]})
        self.__check_hashes(self.fileHashes, md5s)

        return self.fileHashes

    def __hash_file(self, input, hasher):
        filename = os.path.basename(input)
        fh = file(input, 'r')
        chunk = fh.read(self.__BLOCKSIZE)
        while chunk:
            hasher.update(chunk)
            chunk = fh.read(self.__BLOCKSIZE)
        fh.close()
        return {os.path.basename(filename) : hasher.hexdigest()}
        
    def __hash_directory(self, dir, hasher):
        fileHashes = {}
        for filename in os.listdir(dir):
            hash = hasher.copy()
            srcFile = os.path.join(dir, filename)
            fileHashes.update(self.__hash_file(srcFile, hash))
            del hash
        return fileHashes

    def check_signature(self):
        ### FIXME: The trickiest piece of this is that we need to check for
        # signatures in several places: main rpm database.
        # fedora private database
        # gpg keyring
        pass
