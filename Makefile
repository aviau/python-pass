.PHONY: build kill

build:
	sudo docker build -t pypass_image .

kill:
	- sudo docker stop pypass
	- sudo docker rm pypass

run: kill build
	sudo docker run -i -t --name pypass pypass_image bash

test: kill build
	sudo docker run -t --name pypass pypass_image bash -c "cd pypass && tox"

