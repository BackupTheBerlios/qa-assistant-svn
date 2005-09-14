dnl File: configure.ac
dnl Author: Toshio Kuratomi
dnl Date: 27 April, 2004
dnl Description: Controls the configure process for qa-assistant
dnl $Id$

AC_INIT([QA Assistant], [0.4.90.4], [abadger1999@sourceforge.net], [qa-assistant])
AC_CONFIG_SRCDIR([src/qareviewer.py])
AM_INIT_AUTOMAKE([gnu check-news dist-bzip2 -Wall])

AC_SUBST(CHECKLISTVER, [0.3])
AC_SUBST(QASAVEVER, [0.1])

AM_MAINTAINER_MODE

AC_PATH_PROG(GCONFTOOL, gconftool-2)
AM_GCONF_SOURCE_2

AC_PATH_PROG(XMLCATALOG, xmlcatalog)

dnl check for python
AM_PATH_PYTHON([2.3])
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

dnl We're bumping up to pygtk-2.4 for this version so we can embed the
dnl filechooser into the druid.  We may bump to pygtk-2.6 after it's released
dnl so we can drop my optionrenderer hack in favor of gtk.CellRendererCombo.
PKG_CHECK_MODULES(PYGTK, pygtk-2.0 >= 2.4.0)
AC_SUBST(PYGTK_CFLAGS)
AC_SUBST(PYGTK_LIBS)
dnl gnome-python 2.10.0 for gnome.Program.locate_file()
PKG_CHECK_MODULES(PYGNOME, gnome-python-2.0 >= 2.10.0)
AC_SUBST(PYGNOME_CFLAGS)
AC_SUBST(PYGNOME_LIBS)
PKG_CHECK_MODULES(LIBXML, libxml-2.0 >= 2.5.0)
AC_SUBST(LIBXML_CFLAGS)
AC_SUBST(LIBXML_LIBS)

AC_CONFIG_FILES([
Makefile
tests/Makefile
src/Makefile
qa-assistant.spec
src/qaglobals.py
src/qa-assistant.pyin
src/qa-convert.pyin
])
AC_OUTPUT
