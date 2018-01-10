python-pass
###########

.. image:: https://travis-ci.org/ReAzem/python-pass.svg?branch=master
    :target: https://travis-ci.org/ReAzem/python-pass

.. image:: https://img.shields.io/coveralls/ReAzem/python-pass.svg
  :target: https://coveralls.io/r/ReAzem/python-pass?branch=master

.. image:: https://readthedocs.org/projects/pypass/badge/?version=latest&style
    :target: https://readthedocs.org/projects/pypass/
    :alt: Documentation Status


.. image:: https://pypip.in/version/pypass/badge.svg
    :target: https://pypi.python.org/pypi/pypass/
    :alt: Latest Version

For fun, I have decided to write `pass <http://www.passwordstore.org/>`_ in Python.

Python-pass will provide the same functionality as `pass <http://www.passwordstore.org/>`_. In addition, it will be usable as a library.

Testing
+++++++

Python-pass is tested for python 2.7, 3.2, 3.3, 3.4, pypy and pypy3

On your machine
---------------

- Install the requirements: ``sudo apt-get install -y gnupg tree``
- Prepare the gnupg home directory for testing: ``make setup_gpg``
- Run the tests: ``tox``


With Docker
-----------

- Run the tests in a container: ``make test``
- Or, get a shell with pypass installed: ``make run``

Documentation
+++++++++++++

Documentation for python-pass is available on `pypass.rtfd.org <http://pypass.readthedocs.org/>`_.

You can build the documentation and the man page yourself with ``tox -edocs``. The HTML documentation will be built in ``docs/build/html`` and the man page will be built in ``docs/build/man``.

Project Status
++++++++++++++

Bash completion
---------------

Comming soon.


``pypass init``
---------------

- [X] ``pypass init`` -  creates a folder and a .gpg-id file
- [X] Support ``--path`` option
- [ ] re-encryption functionality
- [X] Should output: ``Password store initialized for [gpg-id].``
- [X] ``--clone <url>`` allows to init from an existing repo

``pypass insert``
-----------------

- [X] ``pypass insert test.com`` prompts for a password and creates a test.com.gpg file
- [X] multi-line support
- [X] create a git commit
- [ ] When inserting in a folder with a .gpg-id file, insert should use the .gpg-id file's key

``pypass show``
---------------

- [X] ``pypass show test.com`` will display the content of test.com.gpg
- [X] ``--clip, -c`` copies the first line to the clipboard
- [ ] ``--password``, and ``--username`` options.
    Accepted format:
    ::
        <the_password>
        login: <the_login>
        url: <the_url> 


``pypass connect`` (or ``ssh``)
-------------------------------

This new command should connect to a server using an encrypted rsa key. 

``pypass ls``
-------------

- [X] ``pypass ls`` shows the content of the password store with ``tree``
- [X] ``pypass`` invokes ``pypass ls`` by default
- [X] ``pypass ls subfolder`` calls tree on the subfolder only
- [X] Hide .gpg at the end of each entry
- [X] Accept subfolder argument
- [X] First output line should be ``Password Store``

``pypass rm``
-------------

- [X] ``pypass rm test.com`` removes the test.com.gpg file
- [ ] ``pypass remove`` and ``pypass delete`` aliases
- [X] ``pypass rm -r folder`` (or ``--recursive``)  will remove a folder and all of it's content (not interactive!)
- [X] Ask for confirmation

``pypass find``
---------------

- [X] ``pypass find python.org pypass`` will show a tree with password entries that match python.org or pass
- [X] Accepts one or many search terms

``pypass cp``
-------------

- [X] ``pypass cp old-path new-pah`` copies a password to a new path
- [ ] Dont overwrite

``pypass mv``
-------------

- [X] ``pypass mv old-path new-path`` moves a password to a new path
- [ ] Dont overwrite

``pypass git``
--------------

- [X] Pass commands to git
- [X] ``pypass git init`` should behave differently with an existing password store
- [X] Add tests

``pypass edit``
--------------

- [X] ``pypass edit test.com`` will open a text editor and let you edit the password

``pypass grep``
---------------

- [X] ``pypass grep searchstring`` will search for the given string inside all of the encrypted passwords


``pypass generate``
-------------------
- [ ] ``pypass generate [pass-name] [pass-length]`` Genrates a new password using of length pass-length and inserts it into pass-name.
- [ ] ``--no-symbols, -n``
- [ ] ``--clip, -c``
- [ ] ``--in-place, -i``
- [ ] ``--force, -f``
