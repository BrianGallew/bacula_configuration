Bacula Configuration
====================

Scripts for Bacula configuration management

MOTIVATION
----------

Bacula's worst weakness is configuration.  Adding one more host to your
current setup involves the following steps:

1. Install the client software
2. Create a bacula-fd.conf.  It needs:
 - Director stanza, with new passwords, for each director
 - Messages stanza
 - FileDaemon/Client stanza
3. Update your director(s) configuration:
 - Client entry (with the name and password from bacula-fd.conf)
 - One or more Job entries
 - (Optional) Storage/Pool entries.
 - (Optional) Create new Fileset/Schedule entries
4. (Optional) Update your storage(s) configuration:
 - Pool
 - Storage
 - Device

All that data has to mesh together perfectly, or Bacula won't work.
Admittedly, you can short-circuit some of this by using the same passwords
everywhere and a standard set of directors and only one Message
configuration, and all hosts share the same storage pool and devices.

Then there's auditing.  *You* know perfectly well what hosts are backed up
with which scheuldes, and the filesets involved.  But do your coworkers?
What about your boss?  Do you answer all the questions about which hosts
are backed up, and how, or do you want to delegate all of that to your
front-line support?  How about the possibility of giving your install team
an easy tool for setting up new backups?

Finally, there's maintenance.  Storage servers are taken (temporarily)
offline.  Clients are decommissioned (which means all the jobs left in the
catalog at that point will never be pruned) or change roles.  Directors are
replaced.  New Filesets (and associated Jobs) need to be added to groups of
Clients.  All of these events require tedious, error prone, manual updates.

WHAT IT DOES
------------

CLI tool to import an existing configuration

CLI tools to create/delete/edit all of the resources used by Bacula

CLI tools designed to drop into cron that will keep the director(s) and
storage daemon(s) configuration up-to-date, with appropriate activity
checks around restarts.

Web interface that yields an appropriate bacula-fd.conf like this:
`wget -O /etc/bacula/bacula-fd.conf http://director.example.com/cgi-bin/fd`

CLI tool for updating Confluence with live documentation.  This will
include service and host notes, as well as schedules and filesets (where
possible: filesets that use < syntax will be incomplete).

CURRENT STATUS
--------------

Modulo any bugs, this seems to be complete as a framework.  Tests are
incomplete, though, and I think it could use a little more polish
documentation-wise.  

DEPENDENCIES
-------------

If you do not have mysql-python installed, setuptools will install it as a
dependency.  If you would rather have it installed from an OS package, you
should do that first.

pyparsing is required if and only if you want to import an existing
configuration.  I should note that this is making DRY code difficult, as
adding the parsing bits to the base class would make pyparsing required
everywhere, which is really not desirable.

DATABASE
---------

You'll need to create the database schema using
bacula_tools/data/bacula_configuration.schema 

Today, we are MySQL-only.  Adding support for PostgreSQL shouldn't be
difficult, but I'd have to see a desire for that before doing the work.

OS SETUP
---------

You will need to customize several values, whose defaults are in
bacula_tools/\_\_init\_\_.py.  The easiest way to do so is to drop value
assignments into any/all of the configuration files:

	/etc/bacula/bacula.conf
	/usr/local/etc/bacula/bacula.conf
	/usr/local/etc/bacula.conf
	~/.bacula.conf

The files are read in that order, and all updates applied in that order.
In particular, you will want to set values for:

	MYSQL_DB
	MYSQL_HOST
	MYSQL_USER
	MYSQL_PASS

Here is an example script that will set it all up for you:

	#! /bin/sh
	
	python setup.py install
	mysql -u root -p <<EOF
	create schema baculacfg;
	grant all on baculacfg.* to baculacfg identified by 'baculacfg';
	use baculacfg
	\. bacula_tools/data/bacula_configuration.schema
	EOF
	
	cat > /usr/local/etc/bacula.conf <<EOF
	MYSQL_DB='baculacfg'
	MYSQL_HOST='localhost'
	MYSQL_USER='baculacfg'
	MYSQL_PASS='baculacfg'
	EOF
	
	# import the current configuration
	./bin/import_configuration /etc/bacula/*.conf
	
	exit
