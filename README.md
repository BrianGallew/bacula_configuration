Bacula Configuration
======

Scripts for Bacula configuration management

Install the package this way:
python setup.py install

You'll need to create the database schema using
bacula_configuration.schema 

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

You will probably want to customize _guessing_rules, though that's not as
amenable to configuration (sorry).

pyparsing is required if and only if you want to import an existing
configuration.  Otherwise, it's unneeded.  I should note that this is
making DRY code difficult, as adding the parsing bits to the base class
would make pyparsing required everywhere, which is really not desirable.

