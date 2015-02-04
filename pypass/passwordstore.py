#
#    Copyright (C) 2014 Alexandre Viau <alexandre@alexandreviau.net>
#
#    This file is part of python-pass.
#
#    python-pass is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    python-pass is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with python-pass.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import subprocess
import string
import random
import re

from .entry_type import EntryType

# Find the right gpg binary
if subprocess.call(
        ['which', 'gpg2'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE) == 0:
    GPG_BIN = 'gpg2'
elif subprocess.call(
        ['which', 'gpg'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE) == 0:
    GPG_BIN = 'gpg'
else:
    raise Exception("Could not find GPG")


class PasswordStore(object):
    """This is a Password Store

    :param path: The path of the password-store. By default,
                 '$home/.password-store'.
    :param git_dir: The git directory of the password store. By default,
                    it looks for a .git directory in the password store.
    """

    def __init__(
            self,
            path=os.path.join(os.getenv("HOME"), ".password-store"),
            git_dir=None,
    ):
        self.path = path

        # Read the .gpg-id
        gpg_id_file = os.path.join(path, '.gpg-id')
        if os.path.isfile(gpg_id_file):
            self.gpg_id = open(gpg_id_file, 'r').read().strip()
        else:
            raise Exception("could not find .gpg-id file")

        # Try to locate the git dir
        git_dir = git_dir or os.path.join(self.path, '.git')
        self.uses_git = os.path.isdir(git_dir)
        if self.uses_git:
            self.git_dir = git_dir

    def get_passwords_list(self):
        """Returns a list of the passwords in the store

        :returns: Example: ['Email/bob.net', 'example.com']
        """
        passwords = []

        for root, dirnames, filenames in os.walk(self.path):
            for filename in filenames:
                if filename.endswith('.gpg'):
                    path = os.path.join(root, filename.replace('.gpg', ''))
                    simplified_path = path.replace(self.path + '/', '')
                    passwords.append(simplified_path)

        return passwords

    def get_decypted_password(self, path, entry=None):
        """Returns the content of the decrypted password file

        :param path: The path of the password to be decrypted. Example:
                     'email.com'
        :param entry: The entry to retreive. (EntryType enum)
        """
        passfile_path = os.path.realpath(
            os.path.join(
                self.path,
                path + '.gpg'
            )
        )

        gpg = subprocess.Popen(
            [
                GPG_BIN,
                '--quiet',
                '--batch',
                '--use-agent',
                '-d', passfile_path,
            ],
            shell=False,
            stdout=subprocess.PIPE
        )
        gpg.wait()

        if gpg.returncode == 0:
            decrypted_password = gpg.stdout.read().decode()

            if entry == EntryType.username:
                usr = re.search(
                    '(?:username|user|login): (.+)',
                    decrypted_password
                )
                if usr:
                    return usr.groups()[0]
            elif entry == EntryType.password:
                pw = re.search('(?:password|pass): (.+)', decrypted_password)
                if pw:
                    return pw.groups()[0]
                else:  # If there is no match, password is the first line
                    return decrypted_password.split('\n')[0]
            elif entry == EntryType.hostname:
                hostname = re.search(
                    '(?:host|hostname): (.+)', decrypted_password
                )
                return hostname.groups()[0]
            else:
                return decrypted_password

    def insert_password(self, path, password):
        """Encrypts the password at the given path

        :param path: Where to insert the password. Ex: 'passwordstore.org'
        :param password: The password to insert, can be multi-line
        """

        passfile_path = os.path.realpath(
            os.path.join(self.path, path + '.gpg')
        )

        gpg = subprocess.Popen(
            [
                GPG_BIN,
                '-e',
                '-r', self.gpg_id,
                '--batch',
                '--use-agent',
                '--no-tty',
                '--yes',
                '-o', passfile_path
            ],
            shell=False,
            stdin=subprocess.PIPE
        )

        gpg.stdin.write(password.encode())
        gpg.stdin.close()
        gpg.wait()

    @staticmethod
    def generate_password(digits=True, symbols=True, length=15):
        """Returns a random password

        :param digits: Should the password have digits? Defaults to True
        :param symbols: Should the password have symbols? Defaults to True
        :param length: Length of the password. Defaults to 15
        """

        chars = string.ascii_letters

        if symbols:
            chars += string.punctuation

        if digits:
            chars += string.digits

        password = ''.join(random.choice(chars) for i in range(length))
        return password

    @staticmethod
    def init(gpg_id, path, clone_url=None):
        """Creates a password store to the given path

        :param gpg_id: Default gpg key identification used for encryption and
                       decryption. Example: '3CCC3A3A'
        :param path: Where to create the password store. By default, this is
                     $home/.password-store
        :param clone_url: If specified, the clone_url parameter will be used
                          to import a password store from a git repository.
                          Example: ssh://myserver.net:/home/bob/.password-store
        :returns: PasswordStore object
        """
        git_dir = os.path.join(path, '.git')
        git_work_tree = path

        # Create a folder at the path
        if not os.path.exists(path):
            os.makedirs(path)

        # Clone an existing remote repo
        if clone_url:
            # Init git repo
            subprocess.call(
                [
                    "git",
                    "--git-dir=%s" % git_dir,
                    "--work-tree=%s" % git_work_tree,
                    "init", path
                ],
                shell=False
            )

            # Add remote repo
            subprocess.call(
                [
                    "git",
                    "--git-dir=%s" % git_dir,
                    "--work-tree=%s" % git_work_tree,
                    "remote",
                    "add",
                    "origin",
                    clone_url
                ],
                shell=False,
            )

            # Pull remote repo
            # TODO: add parameters for remote and branch ?
            subprocess.call(
                [
                    "git",
                    "--git-dir=%s" % git_dir,
                    "--work-tree=%s" % git_work_tree,
                    "pull",
                    "origin",
                    "master"
                ],
                shell=False
            )

        gpg_id_path = os.path.join(path, '.gpg-id')
        if os.path.exists(gpg_id_path) is False:
            # Create .gpg_id and put the gpg id in it
            with open(os.path.join(path, '.gpg-id'), 'a') as gpg_id_file:
                gpg_id_file.write(gpg_id + '\n')

        return PasswordStore(path)

    def git_init(self, git_dir=None):
        """Transform  the existing password store into a git repository

        :param git_dir: Where to create the git directory. By default, it will
                        be created at the root of the password store in a .git
                        folder.
        """

        self.git_dir = git_dir or os.path.join(self.path, '.git')
        self.uses_git = True

        subprocess.call(
            [
                'git',
                "--git-dir=%s" % self.git_dir,
                "--work-tree=%s" % self.path,
                'init',
            ],
            shell=False
        )

        self.git_add_and_commit(
            '.',
            message="Add current contents of password store."
        )

        # Create .gitattributes and commit it
        with open(
                os.path.join(self.path, '.gitattributes'), 'w'
        ) as gitattributes:
            gitattributes.write('*.gpg diff=gpg\n')

        self.git_add_and_commit(
            '.gitattributes',
            message="Configure git repository for gpg file diff."
        )

        subprocess.call(
            [
                'git',
                "--git-dir=%s" % self.git_dir,
                "--work-tree=%s" % self.path,
                'config',
                '--local',
                'diff.gpg.binary',
                'true'
            ],
            shell=False
        )

        subprocess.call(
            [
                'git',
                "--git-dir=%s" % self.git_dir,
                "--work-tree=%s" % self.path,
                'config',
                '--local',
                'diff.gpg.textconv',
                'gpg -d'
            ],
            shell=False
        )

    def git_add_and_commit(self, path, message=None):

        subprocess.call(
            [
                'git',
                "--git-dir=%s" % self.git_dir,
                "--work-tree=%s" % self.path,
                'add',
                path
            ],
            shell=False
        )

        if message:
            subprocess.call(
                [
                    'git',
                    "--git-dir=%s" % self.git_dir,
                    "--work-tree=%s" % self.path,
                    'commit',
                    '-m',
                    message
                ],
                shell=False
            )
        else:
            subprocess.call(
                [
                    'git',
                    "--git-dir=%s" % self.git_dir,
                    "--work-tree=%s" % self.path,
                    'commit'
                ],
                shell=False
            )
