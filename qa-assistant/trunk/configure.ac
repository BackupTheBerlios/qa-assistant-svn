dnl File: configure.ac
dnl Author: Toshio Kuratomi
dnl Date: 27 April, 2004
dnl Description: Controls the configure process for qa-assistant
dnl $Id$

AC_INIT([QA Assistant], [0.4], [abadger1999@sourceforge.net], qa-assistant)
AC_CONFIG_SRCDIR([qareviewer.py])
AM_INIT_AUTOMAKE([gnu check-news dist-bzip2 -Wall])

AM_MAINTAINER_MODE

AC_PATH_PROG(GCONFTOOL, gconftool-2)
AM_GCONF_SOURCE_2

dnl check for python
AM_PATH_PYTHON

dnl Unfortunately, some fixes went into 2.2.0 that never made it into 2.0.
dnl so we need at least that version.
PKG_CHECK_MODULES(PYGTK, pygtk-2.0 >= 2.2.0)
AC_SUBST(PYGTK_CFLAGS)
AC_SUBST(PYGTK_LIBS)
PKG_CHECK_MODULES(PYGNOME, gnome-python-2.0)
AC_SUBST(PYGNOME_CFLAGS)
AC_SUBST(PYGNOME_LIBS)

AC_OUTPUT([
Makefile
qa-assistant.spec
])
