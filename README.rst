python-pass
###########

.. image:: https://travis-ci.org/ReAzem/python-pass.svg?branch=master
    :target: https://travis-ci.org/ReAzem/python-pass

.. image:: https://img.shields.io/coveralls/ReAzem/python-pass.svg
  :target: https://coveralls.io/r/ReAzem/python-pass?branch=master

For fun, I have decided to write `pass <http://www.passwordstore.org/>`_ in Python.

Project Status
++++++++++++++

``pypass init``
---------------

- [X] ``pypass init`` -  creates a folder and a .gpg-id file
- [X] Support ``--path`` option
- [ ] re-encryption functionality

``pypass insert``
-----------------

- [X] ``pypass insert test.com`` prompts for a password and creates a test.com.gpg file
- [ ] multi-line support
- [ ] create a git commit

``pypass show``
---------------

- [X] ``pypass show test.com`` will display the content of test.com.gpg

``pypass ls``
-------------

- [X] ``pypass ls`` shows the content of the password store with ``tree``
- [X] ``pypass`` invokes ``pypass ls`` by default
- [ ] Hide .gpg at the end of each entry
- [ ] Accept subfolder argument

``pypass rm``
-------------

- [X] ``pypass rm test.com`` removes the test.com.gpg file
- [ ] ``pypass remove`` and ``pypass delete`` aliases
- [X] ``pypass rm -r folder`` (or ``--recursive``)  will remove a folder and all of it's content (not interactive!)
