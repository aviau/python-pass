Manpage
=======

Synopsis
--------

pypass [COMMAND] [OPTIONS] [ARGS]

Description
-----------

pass  is  a  very  simple  password store that keeps passwords inside gpg2(1) encrypted files inside a simple directory tree residing at ~/.password-store.  The pass utility provides a series of commands for manipulating the password store, allowing the user to add, remove, edit, synchronize, generate, and manipulate passwords.

If no COMMAND is specified, COMMAND defaults to either show  or  ls, depending  on  the type of specifier in ARGS. Otherwise COMMAND must be one of the valid commands listed below.

Several of the commands below rely on or  provide  additional  functionality  if the password store directory is also a git repository. If the password store directory is a git  repository,  all  password store  modification  commands will cause a corresponding git commit. See the EXTENDED GIT EXAMPLE  section  for  a  detailed  description using init and git(1).

The  init command must be run before other commands in order to initialize the password store with the correct gpg  key  id.  Passwords are encrypting using the gpg key set with init.

Commands
--------

.. include:: man/commands.rst

Simple Examples
---------------

Extended Git Example
--------------------

Files
-----

Environement Variables
---------------------

See Also
--------

Author
------

Copying
-------

See Also
--------
:manpage:`gpg2(1)`, :manpage:`pwgen(1)`, :manpage:`git(1)`, :manpage:`xclip(1)`.
