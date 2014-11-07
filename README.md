# python-pass

[![Build Status](https://travis-ci.org/ReAzem/python-pass.svg?branch=master)](https://travis-ci.org/ReAzem/python-pass) [![Coverage Status](https://img.shields.io/coveralls/ReAzem/python-pass.svg)](https://coveralls.io/r/ReAzem/python-pass?branch=master)

For fun, I have decided to write [pass](http://www.passwordstore.org/) in Python.

## Project Status

### ```pypass init```

- [X] ```pypass init``` -  creates a folder and a .gpg-id file
- [X] Support ```--path``` option
- [ ] re-encryption functionality

### ```pypass insert```

- [X] ```pypass insert test.com``` prompts for a password and creates a test.com.gpg file
- [ ] multi-line support
- [ ] create a git commit

### ```pypass show```

- [X] ```pypass show test.com``` will display the content of test.com.gpg

### ```pypass ls```
- [X] ```pypass ls``` shows the content of the password store with ```tree```
- [ ] Hide .gpg at the end of each entry
- [ ] Accept subfolder argument
