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
		SRPM.py \
		checklist.py \
		checkload.py \
		checkview.py \
		error.py \
		gnomeglade.py \
		gpg.py \
		optionrenderer.py \
		preferences.py \
		properties.py \
		propview.py \
		qaapp.py \
		qareviewer.py \
		review.py \
		srpmqa.py \
		treetips.py

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
	    
install-data-hook:
# automake's py_compile script compiles DESTDIR into the module's paths
# which is not what we want.  (DESTDIR is a staging area so it
# shouldn't be included in the built files.)  This takes care of it.
	python -c "import compileall ; compileall.compile_dir('$(DESTDIR)$(qa_assistantdir)', None, '$(qa_assistantdir)', True)"
