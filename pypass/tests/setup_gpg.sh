#!/bin/sh

export REALPATH="$(realpath $(dirname $0))"
export GNUPGHOME="$REALPATH/gnupg"

umask 077
mkdir -p $GNUPGHOME

gpg --allow-secret-key-import --import $REALPATH/test_key_sec.asc
gpg --import-ownertrust $REALPATH/test_ownertrust.txt
