Bacula Configuration
======

Scripts for Bacula configuration management

Install the package this way:
python setup.py install

You'll need to create the database schema using
bacula_configuration.schema 

Finally, site-packages/bacula_configuration/__init__.py will need to be
customized with, at the least, the database privileges.
