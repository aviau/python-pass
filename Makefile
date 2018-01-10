.PHONY: build kill setup_gpg

build:
	sudo docker build -t pypass_image .

kill:
	- sudo docker stop pypass
	- sudo docker rm pypass

run: kill build
	sudo docker run -i -t --name pypass pypass_image bash

test: kill build
	sudo docker run -t --name pypass pypass_image bash -c "cd pypass && tox"

setup_gpg: pypass/tests/gnupg
pypass/tests/gnupg: pypass/tests/test_key_sec.asc pypass/tests/test_ownertrust.txt
	mkdir -m 700 -p pypass/tests/gnupg
	GNUPGHOME=pypass/tests/gnupg gpg --allow-secret-key-import --import pypass/tests/test_key_sec.asc
	GNUPGHOME=pypass/tests/gnupg gpg --import-ownertrust pypass/tests/test_ownertrust.txt
