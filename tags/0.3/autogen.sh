#!/bin/sh
# File: autogen.sh
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 21 October 1999
# Description: This script runs commands necessary to generate a Makefile
# $Id$

echo "Warning: This script will run configure for you -- if you need to pass"
echo "  arguments to configure, please give them as arguments to this script."

aclocal
automake --add-missing
autoconf
./configure $*

exit 0
