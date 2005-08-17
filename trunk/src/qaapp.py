# File: qaapp.py
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 1 May 2005
# Copyright: Toshio Kuratomi
# License: GPL
# Id: $Id$
'''Instantiate one instance of the program.
'''
__revision__ = '$Rev$'

import sys
import qareviewer

app = qareviewer.QAReviewer(sys.argv)
