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
__revision__ = '$Rev$'

import os
import string

from qaconst import *
import error

# With gpgme, this function remains as the get passphrase callback.
# Use gpgme_set_passphrase_cb to set it.
import gtk

def get_passphrase(gpgId, badPass):
    '''Retrieve a passphrase from the user.
    '''
    passDialog = gtk.Dialog('Enter Passphrase', None,
            gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_OK, gtk.RESPONSE_OK,
                gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
    passDialog.set_default_response(gtk.RESPONSE_OK)
    vbox = passDialog.vbox
    # Let the user know if the previous password didn't work.
    if badPass:
        reprompt = gtk.Label('The password you entered did not work.  Please'
        ' try reentering it.')
        reprompt.set_line_wrap(True)
        vbox.add(reprompt)
       
    prompt = gtk.Label('Please enter the passphrase for ' + gpgId)
    prompt.set_line_wrap(True)
    vbox.add(prompt)
    
    passphraseEntry = gtk.Entry()
    passphraseEntry.set_visibility(False)
    vbox.add(passphraseEntry)
    vbox.show_all()

    response = passDialog.run()
    if response == gtk.RESPONSE_OK:
        passphrase = passphraseEntry.get_text()
    else:
        passphrase = None
    
    passDialog.destroy()
    return passphrase

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
    cmd = (pathToGpg + " --local-user '" + gpgID +
            "' --clearsign --armor --status-fd 2 --command-fd 0")
    (gpgIn, gpgOut, gpgStatus) = os.popen3(cmd)
    while True:
        gpgString = gpgStatus.readline().split(None, 2)
        if gpgString[1] == 'GET_HIDDEN':
            gpgIn.writelines((passphrase, '\n'))
            gpgIn.flush()
        elif gpgString[1] == 'GOOD_PASSPHRASE':
            gpgIn.write(buf)
            gpgIn.close()
        elif gpgString[1] == 'SIG_CREATED':
            outBuf = gpgOut.read()
            break
        elif gpgString[1] == 'BAD_PASSPHRASE':
            gpgIn.close()
            gpgOut.close()
            gpgStatus.close()
            raise error.BadPassphrase
        elif gpgString[1] == 'NO_SECKEY':
            gpgIn.close()
            gpgOut.close()
            gpgStatus.close()
            raise error.NoSecretKey
    gpgIn.close()
    gpgOut.close()
    gpgStatus.close()
    if not outBuf:
        raise error.outBuf
    return outBuf
