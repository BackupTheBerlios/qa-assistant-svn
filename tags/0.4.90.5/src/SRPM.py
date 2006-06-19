# File: SRPM.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 27 March 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
__revision__ = "$Rev$"

#
# Hash generating and checking 
# 
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
