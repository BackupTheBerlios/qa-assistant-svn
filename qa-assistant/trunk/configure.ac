dnl File: configure.ac
dnl Author: Toshio Kuratomi
dnl Date: 27 April, 2004
dnl Description: Controls the configure process for qa-assistant
dnl $Id$

AC_INIT([QA Assistant], [0.4.90.1], [abadger1999@sourceforge.net], qa-assistant)
AC_CONFIG_SRCDIR([qareviewer.py])
AM_INIT_AUTOMAKE([gnu check-news dist-bzip2 -Wall])

AC_SUBST(CHECKLISTVER, [0.3])
AC_SUBST(QASAVEVER, [0.1])

AM_MAINTAINER_MODE

AC_PATH_PROG(GCONFTOOL, gconftool-2)
AM_GCONF_SOURCE_2

AC_PATH_PROG(XMLCATALOG, xmlcatalog)

dnl check for python
AM_PATH_PYTHON([2.2])
if test x$PYTHON_VERSION = x'2.2'; then
	AC_MSG_CHECKING([for python textwrap module])
	if python -c 'import optik.textwrap' &>/dev/null; then
		AC_MSG_RESULT([yes])
	elif python -c 'import optparse.textwrap' &>/dev/null; then
		AC_MSG_RESULT([yes])
	else
		AC_MSG_RESULT([no])
		AC_MSG_ERROR([
		textwrap module from the python-2.3 standard library or
		Greg Ward's Optik module (http://optik.sf.net) are needed to
		have a functioning qa-assistant.
		Please install one or the other before proceeding.])
	fi
fi

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
tests/Makefile
qa-assistant.spec
qaconst.py
])
