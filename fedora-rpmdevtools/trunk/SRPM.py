# File: SRPM.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 27 March 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
"""A representation of an SRPM.
"""
__revision__ = "$Revision$"

import rpm
import os, sys, stat
import md5
import gzip

__PYVER = int(float(sys.version[:3])*100)
if __PYVER >= 230:
    __HAS_BZ2 = True
    import bz2


class SRPM:
    __PYVER = int(float(sys.version[:3])*100)
    __BLOCKSIZE=8192
    def __init__(self, SRPMFile):
        self.filename=os.path.abspath(SRPMFile)
        ### FIXME: Really I should just check to be sure the file exists.
        # The filehandle only has to be obtained for a limited time in one
        # situation.
        try:
            os.access(self.filename, os.R_OK)
        except:
            sys.stderr.write("Unable to read SRPM file %s\n" % (self.filename))
            ### FIXME: Exceptions
            return False
        self.expanded = False
        self.expandDir = None
        
        transSet = rpm.TransactionSet()
        transSet.setVSFlags(~(rpm._RPMVSF_NOSIGNATURES |
                            rpm._RPMVSF_NODIGESTS | rpm.RPMVSF_NOHDRCHK))
        ### FIXME: rpm2cpio does this disabling, but it may not be a good idea
        # since we want to know if there's anything strange and wrong about
        # the rpm (unlike rpm2cpio whose only mission is to get the payload
        # out.  Not sure when this actually fails, though.
        # Make a decision to keep or not keep this.
        #transSet.setVSFlags(~(rpm._RPMVSF_NOSIGNATURES |
        #                    rpm.RPMVSF_NODIGESTS | rpm.RPMVSF_NOHDRCHK))
        filehandle = file(self.filename)
        self.hdr = transSet.hdrFromFdno(filehandle.fileno())
        self.payloadOffset = filehandle.tell()
        del transSet

        self.compressMethod = self.hdr[rpm.RPMTAG_PAYLOADCOMPRESSOR] or 'gzip'
        self.NVR = (self.hdr[rpm.RPMTAG_NAME] + '-' + 
                self.hdr[rpm.RPMTAG_VERSION] + '-' +
                self.hdr[rpm.RPMTAG_RELEASE])
        self.__calc_hashes()

    def unarchive(self, directory=None):
        """Moves the files from the RPM Payload into a directory

        """
        if directory == None:
            ### FIXME: get directory from GConf2
            directory = '/home/badger/rpmbuild/SOURCES'
        ### FIXME: the old way of doing things
        unrpmDirectory = directory
        ### FIXME: Use this when we get our internal rpm2cpio working
        directory+='/'+self.NVR
        try:
            ### FIXME: Have to check for previous version of the expanded directory and what we should do about it.  User popup?
            os.mkdir(directory)
        except:
            sys.stderr.write("Unable to create directory %s.\n" % (directory))
            ### FIXME: Exceptions for this class: Security, file access
            return False
        os.chmod(directory, stat.S_IRWXU)
        if os.listdir(directory):
            sys.stderr.write("SECURITY: Somebody changed the directory we were going to write into!")
            ### FIXME: Exceptions
            return False
        """
        filehandle = file(self.filename)
        filehandle.seek(self.payloadOffset)
        if self.compressMethod == 'gzip':
            fd = gzip.GzipFile(None, 'rb', None, filehandle.fileno())
        elif self.compressMethod == 'bzip2':
            if (__HAS_BZ2):
                fd = bz2.BZ2File(None, 'rb', None, filehandle.fileno())
            else:
                sys.stderr.write('No support for payload compressor %s\n' %(compressMethod))
                ### FIXME: Exceptions
                return False
        else:
            sys.stderr.write('Unknown payload compressor %s\n' %(compressMethod))
            return False
        cmd = 'cpio -idum --no-absolute-filenames --force-local --quiet ' + directory
        print cmd
        cpio = os.popen(cmd, 'w', self.__BLOCKSIZE)
        while True:
            buffer = fd.read(self.__BLOCKSIZE)
            if buffer == "": break
            cpio.write(buffer)
        cpio.close()
        fd.close()
        filehandle.close()
        """
        ### FIXME: Try to get the above code working.  Then we can replace
        # this system call with that.
        os.system("fedora-unrpm -C %s %s &>/dev/null" % (unrpmDirectory, self.filename))
        
        self.expandDir = directory
        self.expanded = True

    def hashes(self):
        """Returns the MD5 hashes of the files in the SRPM."""
        return self.srpmHash, self.fileHashes

    def __calc_hashes(self, hashType = None):
        if not hashType:
            hashType = 'md5'
        if not self.expanded:
            self.unarchive()
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
        for filename in self.fileHashes.keys():
            if SRPM.__PYVER >= 230:
                rHash = md5s.pop(filename, None)
            else:
                rHash = md5s.get(filename, None)
            if (rHash == None):
                if (filename == os.path.basename(self.filename)):
                    # No reason to  panic: it's the SRPM file itself
                    continue
                ### FIXME: Exception
                sys.stderr.write("SECURITY: %s is in the package but not listed in the rpm headers.\n" % (filename))
                return False
            if rHash != self.fileHashes[filename]:
                ### FIXME: Exception
                sys.stderr.write("SECURITY: %s has an incorrect MD5 hash in the rpm headers.\n" % (filename))
                return False
            if SRPM.__PYVER < 230:
                del md5s[filename]

        if len(md5s) > 0:
            ### FIXME: Exception
            sys.stderr.write("SECURITY: There are files listed in the rpm header that aren't really there.\n")
            for noFile in md5s:
                sys.stderr.write(" %s\n" %(noFile))
            return False

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
            srcFile = dir+'/'+filename
            fileHashes.update(self.__hash_file(srcFile, hash))
            del hash
        return fileHashes

    def __check_hashes(self):
        pass

    def check_signature(self):
        ### FIXME: The trickiest piece of this is that we need to check for
        # signatures in several places: main rpm database.
        # fedora private database
        # gpg keyring
        pass
