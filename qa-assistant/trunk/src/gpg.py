# File: gpg.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 27 Nov 2004
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
'''Invoke gpg from here.

Eventually we may want all of these to be superceded by gpgme calls.  OTOH
gpgme enables C code to use gpg the way a scripting language would.  Since
python is a glue language anyhow....
'''
__version__ = '0.1'
__revision__ = '$Rev$'

import os
import string

from qaconst import *
import error

def list_secret_keys(pathToGpg):
    ''' List the secret key identities available for the user.
    '''
    secretKeyList = []
    cmd = pathToGpg + ' --list-secret-keys --with-colons'
    GPG = os.popen(cmd)
    for record in GPG.readlines():
        recordArray = string.split(record, ':')
        if recordArray[0] == 'sec':
            secretKeyList.append(recordArray[9])
    GPG.close()
    return secretKeyList

def sign_buffer(buf, gpgID, pathToGpg, passphrase):
    '''Sign an in-memory buffer.
    '''
    cmd = pathToGpg+' --local-user '+gpgID+' --clearsign --armor --status-fd 0'
    (gpgIn, gpgOut, gpgStatus) = os.popen3(cmd)
    for line in gpgStatus.readlines():
        if line[:25] == '[GNUPG:] NEED_PASSPHRASE ':
            gpgIn.write(passphrase)
        elif line == '[GNUPG:] GOOD_PASSPHRASE':
            gpgIn.write(buf)
        elif line[:21] == '[GNUPG:] SIG_CREATED ':
            outBuf = gpgOut.read()
        elif line == '[GNUPG:] BAD_PASSPHRASE':
            raise error.BadPassphrase
        elif line == '[GNUPG:] NO_SECKEY':
            raise error.NoSecretKey
    gpgIn.close()
    gpgOut.close()
    gpgStatus.close()
    if not outBuf:
        raise error.NoOut
    return outBuf
