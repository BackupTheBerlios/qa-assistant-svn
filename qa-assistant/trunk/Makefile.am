# File: Makefile.am
# Author: Toshio Kuratomi <toshio@tiki-lounge.com>
# Date: 27 April, 2004
# Description: Toplevel Makefile.am for the program.  Currently controls the
# making and distribution of the whole program.
# $Id$

SUBDIRS = tests src

qa_assistantdir = $(datadir)/qa-assistant

iconsdir = $(datadir)/pixmaps
icons_DATA = pixmaps/qa-icon.png

#pixmapsdir = $(datadir)/pixmaps/qa-assistant
#pixmaps_DATA = pixmaps/qa-logo.png

dtddir = $(datadir)/xml/qa-assistant
rootcatdir = $(sysconfdir)/xml
ROOTCATALOG=$(rootcatdir)/catalog
CATALOG=$(dtddir)/xmlcatalog
checklistdtddir = $(dtddir)/checklist/$(CHECKLISTVER)
qasavedtddir = $(dtddir)/qasave/$(QASAVEVER)
checklistdtd_DATA = data/checklist.dtd
qasavedtd_DATA = data/qasave.dtd

datafilesdir = $(qa_assistantdir)/data
datafiles_DATA = data/fedoraus.xml \
		 data/fedoraus.py \
		 data/softwarerelease.xml

noinst_DATA = data/minimal-valid.xml

uifilesdir = $(qa_assistantdir)/glade
uifiles_DATA = glade/qa-assistant.glade \
	glade/qa-assistant.gladep \
	glade/qa-assistant.strings

Desktopdir = $(datadir)/applications
Desktop_in_files = qa-assistant.desktop.in
Desktop_DATA = $(Desktop_in_files:.desktop.in=.desktop)
	
schemadir = @GCONF_SCHEMA_FILE_DIR@
schema_in_files = qa-assistant.schemas.in
schema_DATA = $(schema_in_files:.schemas.in=.schemas)

# remove xml catalogs from the check
distuninstallcheck_listfiles = find $(prefix) -type f -not -path $(ROOTCATALOG) -not -path $(CATALOG) -print

# Need to use INTLTOOL to do this when we i18n the code
$(Desktop_DATA): $(Desktop_in_files)
	cp $< $@

EXTRA_DIST = \
	PREFERENCES \
	TODO \
	BUGS \
	autogen.sh \
	qa-assistant.spec \
	qa-assistant.spec.in \
	$(datafiles_DATA) \
	$(noinst_DATA) \
	$(checklistdtd_DATA) \
	$(qasavedtd_DATA) \
	$(uifiles_DATA) \
	$(Desktop_in_files)	\
	$(Desktop_DATA)		\
	$(schema_DATA)	\
	$(icons_DATA)		

CLEANFILES= \
	   qa-assistant*.tar.*

if GCONF_SCHEMAS_INSTALL
install-data-local: $(schema_DATA)
	GCONF_CONFIG_SOURCE=$(GCONF_SCHEMA_CONFIG_SOURCE) \
			    $(GCONFTOOL) --makefile-install-rule $<
else
install-data-local:
endif
			    
install-data-hook:
# Rules to install the DTDs into the system xmlcatalog
# Create subcatalog
	if test ! -f $(DESTDIR)$(CATALOG); then \
		$(XMLCATALOG) --noout --create $(DESTDIR)$(CATALOG); \
	fi
# Add entries to it
	if test -w $(DESTDIR)$(CATALOG); then \
		$(XMLCATALOG) --noout --add "public" \
		"-//BadgerWare//DTD QA Assistant Checklist File $(CHECKLISTVER)//EN" \
		"checklist/$(CHECKLISTVER)/checklist.dtd" $(DESTDIR)$(CATALOG); \
		$(XMLCATALOG) --noout --add "rewriteSystem" \
		"http://qa-assistant.sf.net/dtds/checklist/$(CHECKLISTVER)" \
		"checklist/$(CHECKLISTVER)/" $(DESTDIR)$(CATALOG); \
		$(XMLCATALOG) --noout --add "rewriteURI" \
		"http://qa-assistant.sf.net/dtds/checklist/$(CHECKLISTVER)" \
		"checklist/$(CHECKLISTVER)/" $(DESTDIR)$(CATALOG); \
		$(XMLCATALOG) --noout --add "public" \
		"-//BadgerWare//DTD QA Assistant Save File $(QASAVEVER)//EN" \
		"qasave/$(QASAVEVER)/qasave.dtd" $(DESTDIR)$(CATALOG); \
		$(XMLCATALOG) --noout --add "rewriteSystem" \
		"http://qa-assistant.sf.net/dtds/qasave/$(QASAVEVER)" \
		"qasave/$(QASAVEVER)/" $(DESTDIR)$(CATALOG); \
		$(XMLCATALOG) --noout --add "rewriteURI" \
		"http://qa-assistant.sf.net/dtds/qasave/$(QASAVEVER)" \
		"qasave/$(QASAVEVER)/" $(DESTDIR)$(CATALOG); \
	fi
# Install delegation into the root catalog
	if test ! -f $(DESTDIR)$(ROOTCATALOG); then \
		test -z $(DESTDIR)$(rootcatdir) || \
			$(mkdir_p) $(DESTDIR)$(rootcatdir) ;\
		$(XMLCATALOG) --noout --create  $(DESTDIR)$(ROOTCATALOG); \
	fi
	if test -w $(DESTDIR)$(ROOTCATALOG); then \
		$(XMLCATALOG) --noout --add "delegatePublic" \
			"-//BadgerWare//DTD QA Assistant" \
			"file://$(CATALOG)" $(DESTDIR)$(ROOTCATALOG); \
		$(XMLCATALOG) --noout --add "delegateSystem" \
			"http://qa-assistant.sf.net/dtds" \
			"file://$(CATALOG)" $(DESTDIR)$(ROOTCATALOG); \
		$(XMLCATALOG) --noout --add "delegateURI" \
			"http://qa-assistant.sf.net/dtds" \
			"file://$(CATALOG)" $(DESTDIR)$(ROOTCATALOG); \
	fi
