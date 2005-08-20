#! /usr/bin/python
#
# File: gen-hash.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 17 Aug, 2005
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
'''Usage: gen-hash.py [directory]

gen-hash.py generates cryptographic hashes of checklist functions files and
enters the results into the checklists.
'''
__version__ = '0.1'
__revision__ = '$Rev$'

import os
import sys
import sha
import libxml2

xmlFileDir = sys.argv[1]
for f in os.listdir(sys.argv[1]):
    if f.endswith('.xml'):
        xmlFilename = os.path.join(xmlFileDir, f)
        ctxt = libxml2.newParserCtxt()
        checkList = ctxt.ctxtReadFile(xmlFilename, None, 0)
        root = checkList.getRootElement()
        functions = root.xpathEval2('/checklist/functions')
        if not functions:
            continue
        funcFilename = os.path.join(xmlFileDir, functions[0].content)
        funcFile = file(funcFilename, 'r')
        hasher = sha.new()
        for line in funcFile.readlines():
            hasher.update(line)
        sum = hasher.hexdigest()
        functions[0].setProp('hash', sum)
        functions[0].setProp('hashtype', 'sha1')
        checkList.saveFormatFileEnc(xmlFilename, 'UTF-8', True)
sys.exit(0)
