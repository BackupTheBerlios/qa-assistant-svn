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

class FileError(Exception):
    """Exception raised when there's problems reading the SRPM file."""
    def __init__(self, message, *data):
        self.message = message
        self.args = data
    def __str__(self):
        return repr(self.message)

class SecurityError(Error):
    """
    id:  1   Created a directory and it was changed before we could use it
         100 File is in the first list but not the second
         101 MD5 hash does not match
         102 Files are in the second list but not the first
    """
    def __init__(self, id, filename, message):
        Error.__init__(self, message)
        self.id = id
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
        try:
            self.hdr = transSet.hdrFromFdno(filehandle.fileno())
        except rpm.error:
            raise FileError ("Unable to read the file's rpm header: are you sure it's an rpm file?")
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
                raise SecurityError(1, directory, "Somebody changed %s right after we created it." % (directory))
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
                    raise SecurityError(1, tempDir, "Somebody changed %s right after we created it." % (tempDir))

            # Unarchive our rpm to the tempDir
            self.__unarchive(tempDir)
            hasher = md5.new()
            try:
                oldHashes = self.__hash_directory(directory, hasher)
            except FileError:
                # Allow this to go on because the user might have a
                # temporary directory from the previous expansion
                cla, err = sys.exc_info()[:2]
                try:
                    errArgs = err.__dict__['args']
                except:
                    errArgs = None
                if errArgs:
                    oldHashes = errArgs[1]
                else:
                    oldHashes = []
                    
            pristineHashes = self.__hash_directory(tempDir, hasher)
            try:
                self.__check_hashes(oldHashes, pristineHashes)
            except SecurityError:
                os.path.walk(tempDir, self.__recursive_rm_dir, None)
                raise FileError("%s, which has modified files, is in the way of running the program again.  Please move or remove the directory or use a different directory for expanding SRPMs." % (directory))
            else:
                os.path.walk(tempDir, self.__recursive_rm_dir, None)
        else:
            raise FileError("There's a file in the way of our unarchiving to directory %s.  Please move or remove the offending file or use a different directory for expanding SRPMs." % (directory))

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


    def check_signature(self):
        ### FIXME: The trickiest piece of this is that we need to check for
        # signatures in several places: main rpm database.
        # fedora private database
        # gpg keyring
        pass

    #
    # Hash generating and checking 
    # 
    def __hash_file(self, input, hasher):
        """Hashes a file
        
        Keyword -- arguments:
        input: filename to hash
        hasher: hash function to use
        
        Returns: dictionary of filename : hash
        """
        filename = os.path.basename(input)
        fh = file(input, 'r')
        chunk = fh.read(self.__BLOCKSIZE)
        while chunk:
            hasher.update(chunk)
            chunk = fh.read(self.__BLOCKSIZE)
        fh.close()
        return {os.path.basename(filename) : hasher.hexdigest()}
        
    def __hash_directory(self, dir, hasher):
        """ Hashes a directory of files.
        
        Keyword -- arguments:
        dir: directory name to hash files in
        hasher: hash function to use

        Currently, if the directory contains subdirs, we will continue to hash
        all the files, then raise a FileError regarding unexpected subdirs.
        This allows us to recover if we expect subdirectories to exist.

        Returns: a dictionary of filenames : hashes
        """

        ### FIXME: Someday I plan an enhancement to allow a function argument
        # recurse = True|False to either count subdirectories as errors or
        # recurse.

        fileHashes = {}
        directories=[]
        for filename in os.listdir(dir):
            srcFile = os.path.join(dir, filename)
            if (os.path.isdir(srcFile)):
                directories.append(filename)
                break
            hash = hasher.copy()
            fileHashes.update(self.__hash_file(srcFile, hash))
            del hash

        if len(directories) > 0:
            raise FileError("Unexpected Subdirs", fileHashes)

        return fileHashes

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
        try:
            self.__check_hashes(self.fileHashes, md5s)
        except SecurityError:
            excName, exc = sys.exc_info()[:2]
            # Need to change this to use sys.exc_info because there's some
            # error going on here.
            if exc.id == 100:
                raise SecurityError(exc.id, exc.filename, "%s is in the archive but not listed in the rpm headers" % (exc.filename))
            elif exc.id == 101:
                raise SecurityError(exc.id, exc.filename, "MD5 hash in the headers does not match actual hash for %s" % (exc.filename))
            elif exc.id == 102:
                raise SecurityError(exc.id, exc.filename, "Files listed in the rpm headers do not exist in the archive")

        return self.fileHashes

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
                raise SecurityError(100, filename, "%s is in the first list but not the second" % (filename))
            if rHash != fileHashes[filename]:
                raise SecurityError(101, filename, "MD5 hash does not match for %s" % (filename))
            if SRPM.__PYVER < 230:
                del md5s[filename]

        if len(md5s) > 0:
            filenames = []
            for noFile in md5s:
                filenames.append(noFile)
            raise SecurityError(102, filenames, "Files in the second list do not exist in the first")
