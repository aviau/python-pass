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


class PasswordStore(object):
    """This is a Password Store"""

    def __init__(
            self,
            path=os.path.join(os.getenv("HOME"), ".password-store"),
    ):
        self.path = path

        gpg_id_file = os.path.join(path, '.gpg-id')
        if os.path.isfile(gpg_id_file):
            self.gpg_id = open(gpg_id_file, 'r').read()
        else:
            raise Exception("could not find .gpg-id file")

        self.uses_git = os.path.isdir(
            os.path.join(self.path, '.git')
        )

    def get_passwords_list(self):
        """Returns a list of the passwords in the store"""
        passwords = []

        for root, dirnames, filenames in os.walk(self.path):
            for filename in filenames:
                if filename.endswith('.gpg'):
                    path = os.path.join(root, filename.replace('.gpg', ''))
                    simplified_path = path.replace(self.path + '/', '')
                    passwords.append(simplified_path)

        return passwords

    def get_decypted_password(self, path):
        """Returns the content of the decrypted password file"""
        passfile_path = os.path.realpath(
            os.path.join(
                self.path,
                path + '.gpg'
            )
        )

        gpg = subprocess.Popen(
            [
                'gpg2',
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
            return gpg.stdout.read().decode()

    def insert_password(self, path, password):
        """Encrypts the password to the given path"""

        passfile_path = os.path.realpath(
            os.path.join(self.path, path + '.gpg')
        )

        gpg = subprocess.Popen(
            [
                'gpg2',
                '-e',
                '-r', self.gpg_id,
                '--batch',
                '--use-agent',
                '--no-tty',
                '-o', passfile_path
            ],
            shell=False,
            stdin=subprocess.PIPE
        )

        gpg.stdin.write(password.encode())
        gpg.stdin.close()
        gpg.wait()

    @staticmethod
    def init(gpg_id, path, clone_url=None):
        """Creates a password store to the given path"""
        git_dir = os.path.join(path, '.git')
        git_work_tree = path

        # Create a folder at the path
        if not os.path.exists(path):
            os.makedirs(path)

        # Clone an existing remote repo
        if clone_url:
            # Init git repo
            subprocess.Popen(
                [
                    "git",
                    "--git-dir=%s" % git_dir,
                    "--work-tree=%s" % git_work_tree,
                    "init", path
                ],
                shell=False
            ).wait()

            # Add remote repo
            subprocess.Popen(
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
            ).wait()

            # Pull remote repo
            # TODO: add parameters for remote and branch ?
            subprocess.Popen(
                [
                    "git",
                    "--git-dir=%s" % git_dir,
                    "--work-tree=%s" % git_work_tree,
                    "pull",
                    "origin",
                    "master"
                ],
                shell=False
            ).wait()

        gpg_id_path = os.path.join(path, '.gpg-id')
        if os.path.exists(gpg_id_path) is False:
            # Create .gpg_id and put the gpg id in it
            with open(os.path.join(path, '.gpg-id'), 'a') as gpg_id_file:
                gpg_id_file.write(gpg_id)

        return PasswordStore(path)
