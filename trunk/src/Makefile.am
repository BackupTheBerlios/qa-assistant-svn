# File: Makefile.am
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 27 April, 2004
# Description: Toplevel Makefile.am for the program.  Currently controls the
# making and distribution of the whole program.
# $Id$

bin_SCRIPTS = qa-assistant qa-convert

qa-convert: qa-assistant
qa-assistant: paths.py \
	qaglobals.py

qa_assistantdir = $(datadir)/qa-assistant

qa_assistant_PYTHON = \
		checklist.py \
		checkload.py \
		checkview.py \
		error.py \
		functions.py \
		gnomeglade.py \
		gpg.py \
		optionrenderer.py \
		preferences.py \
		properties.py \
		propview.py \
		qareviewer.py \
		review.py \
		treetips.py \
		ui.py

# Generated program files
nodist_qa_assistantdir = $(datadir)/qa-assistant
nodist_qa_assistant_PYTHON = paths.py \
			     qaglobals.py

noinst_PYTHON = qa-assistant.pyin \
		qa-convert.pyin
EXTRA_DIST = \
	paths.py.pyin \
	qa-assistant.pyin.in \
	qa-convert.pyin.in \
	qaglobals.py.in

CLEANFILES= \
	   $(nodist_qa_assistant_PYTHON) \
	   qa-assistant \
	   qa-convert \
	   *.pyc \
	   *.pyo

%: %.pyin
	sed -e "s,@#datadir#@,$(datadir)," \
	    -e "s,@#libdir#@,$(libdir)," \
	    -e "s,@#prefix#@,$(prefix)," \
	    -e "s,@#sysconfdir#@,$(sysconfdir)," \
	    -e "s,@#pkgdatadir#@,$(pkgdatadir)," < $<  > $@
