bin_SCRIPTS = qa-assistant
qa-assistant: paths.py

qa_assistantdir = $(datadir)/qa-assistant

qa_assistant_PYTHON = \
		SRPM.py \
		checklist.py \
		genericqa.py \
		gnomeglade.py \
		optionrenderer.py \
		properties.py \
		qareviewer.py \
		review.py \
		srpmqa.py \
		treetips.py

# Generated program files
nodist_qa_assistantdir = $(datadir)/qa-assistant
nodist_qa_assistant_PYTHON = \
			paths.py

iconsdir = $(datadir)/pixmaps
icons_DATA = pixmaps/qa-icon.png

#pixmapsdir = $(datadir)/pixmaps/qa-assistant
#pixmaps_DATA = pixmaps/qa-logo.png

datafilesdir = $(qa_assistantdir)/data
datafiles_DATA = data/checklist.dtd \
	data/fedoraus.xml

uifilesdir = $(qa_assistantdir)/glade
uifiles_DATA = glade/qa-assistant.glade \
	glade/qa-assistant.gladep \
	glade/qa-assistant.strings

Desktopdir = $(datadir)/applications
Desktop_in_files = qa-assistant.desktop.in
Desktop_DATA = $(Desktop_in_files:.desktop.in=.desktop)

# Need to use INTLTOOL to do this when we i18n the code
$(Desktop_DATA): $(Desktop_in_files)
	cp $< $@

EXTRA_DIST = \
	PREFERENCES \
	TODO \
	qa-assistant.pyin \
	paths.py.pyin \
	autogen.sh \
	qa-assistant.spec \
	qa-assistant.spec.in \
	$(datafiles_DATA) \
	$(uifiles_DATA) \
	$(Desktop_in_files)	\
	$(Desktop_DATA)		\
	$(icons_DATA)		

CLEANFILES= \
	   $(nodist_qa_assistant_PYTHON) \
	   qa-assistant \
	   *.pyc \
	   *.pyo \
	   qa-assistant*.tar.*

%: %.pyin
	sed -e "s,@#datadir#@,$(datadir)," \
	    -e "s,@#libdir#@,$(libdir)," \
	    -e "s,@#prefix#@,$(prefix)," \
	    -e "s,@#sysconfdir#@,$(sysconfdir)," \
	    -e "s,@#pkgdatadir#@,$(pkgdatadir)," < $<  > $@

install-data-hook:
	# automake's py_compile script compiles DESTDIR into the module's paths
	# which is not what we want.  (DESTDIR is a stagign area so it
	# shouldn't be included in the built files.)  This takes care of it.
	python -c "import compileall ; compileall.compile_dir('$(DESTDIR)$(qa_assistantdir)', None, '$(qa_assistantdir)', True)"
