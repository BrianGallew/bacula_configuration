Bacula Configuration
======

Scripts for Bacula configuration management

DEPENDENCIES:

If you do not have mysql-python installed, setuptools will install it as a
dependency.  If you would rather have it installed from an OS package, you
should do that first.

pyparsing is required if and only if you want to import an existing
configuration.  Otherwise, it's unneeded.  I should note that this is
making DRY code difficult, as adding the parsing bits to the base class
would make pyparsing required everywhere, which is really not desirable.

DATABASE:

You'll need to create the database schema using
bacula_tools/data/bacula_configuration.schema 

OS SETUP:

Finally, you will need to customize several values, whose defaults are in
bacula_tools/__init__.py.  The easiest way to do so is to drop value
assignments into any/all of the configuration files:
	/etc/bacula/bacula.conf
	/usr/local/etc/bacula/bacula.conf
	/usr/local/etc/bacula.conf
	~/.bacula.conf

The files are read in that order, and all updates applied in that order.
In particular, you will want to look at things like:
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
