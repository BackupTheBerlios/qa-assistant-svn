AC_INIT([QA Assistant], [0.3], [abadger1999@sourceforge.net], qa-assistant)
AC_CONFIG_SRCDIR([qareviewer.py])
AM_INIT_AUTOMAKE([gnu check-news dist-bzip2 -Wall])

AM_MAINTAINER_MODE

AC_PATH_PROG(GCONFTOOL, gconftool-2)
AM_GCONF_SOURCE_2

dnl check for python
AM_PATH_PYTHON

PKG_CHECK_MODULES(PYGTK, pygtk-2.0)
AC_SUBST(PYGTK_CFLAGS)
AC_SUBST(PYGTK_LIBS)

AC_OUTPUT([
Makefile
qa-assistant.spec
])
