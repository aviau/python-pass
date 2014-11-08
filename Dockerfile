FROM debian:testing

RUN apt-get update
RUN apt-get install -y git python-pip tree gnupg python3 pypy
RUN pip install tox

ADD pypass pypass/pypass
ADD setup.py pypass/setup.py
ADD setup.cfg pypass/setup.cfg
ADD requirements.txt pypass/requirements.txt
ADD test-requirements.txt pypass/test-requirements.txt
ADD README.rst pypass/README.rst
ADD tox.ini pypass/tox.ini
ADD .git pypass/.git

RUN gpg --allow-secret-key-import --import pypass/pypass/tests/test_key_sec.asc
RUN gpg --import-ownertrust pypass/pypass/tests/test_ownertrust.txt

RUN pip install -r pypass/requirements.txt
RUN cd pypass && python setup.py install

