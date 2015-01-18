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

import unittest
import os
import shutil
import subprocess
import string
import tempfile

from pypass import PasswordStore
from pypass import EntryType


class TestPasswordStore(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()

        # .gpg_id file
        with open(os.path.join(self.dir, '.gpg-id'), 'w') as gpg_id_file:
            gpg_id_file.write('5C5833E3')

        # Create three dummy files
        open(os.path.join(self.dir, 'linux.ca.gpg'), 'a').close()
        open(os.path.join(self.dir, 'passwordstore.org.gpg'), 'a').close()
        open(os.path.join(self.dir, 'test.com.gpg'), 'a').close()

        # Create one folder
        email_folder_path = os.path.join(self.dir, 'Email')
        os.mkdir(email_folder_path)
        open(os.path.join(email_folder_path, 'email.com.gpg'), 'a').close()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_constructor(self):
        store = PasswordStore(self.dir)
        self.assertEqual(store.gpg_id, '5C5833E3')
        self.assertFalse(store.uses_git)
        self.assertEqual(self.dir, store.path)

    def test_get_passwords_list(self):
        store = PasswordStore(self.dir)
        self.assertListEqual(
            sorted(store.get_passwords_list()),
            sorted([
                'test.com',
                'linux.ca',
                'passwordstore.org',
                'Email/email.com',
            ])
        )

    def test_encrypt_decrypt(self):
        self.assertFalse(
            os.path.isfile(os.path.join(self.dir, 'hello.com.gpg'))
        )

        store = PasswordStore(self.dir)
        password = 'ELLO'
        store.insert_password('hello.com', password)

        self.assertTrue(
            os.path.isfile(os.path.join(self.dir, 'hello.com.gpg'))
        )

        self.assertEqual(
            password,
            store.get_decypted_password('hello.com')
        )

    def test_get_decypted_password_specific_entry(self):
        store = PasswordStore(self.dir)
        password = 'ELLO'
        store.insert_password('hello.com', password)

        # When there is no 'password:' mention, the password is assumed to be
        # the first line.
        self.assertEqual(
            'ELLO',
            store.get_decypted_password('hello.com', entry=EntryType.password)
        )

        store.insert_password('hello.com', 'sdfsdf\npassword: pwd')
        self.assertEqual(
            'pwd',
            store.get_decypted_password('hello.com', entry=EntryType.password)
        )

        store.insert_password('hello.com', 'sdf\npassword: pwd\nusername: bob')
        self.assertEqual(
            'bob',
            store.get_decypted_password('hello.com', entry=EntryType.username)
        )

    def test_get_decrypted_password_only_password(self):
        store = PasswordStore(self.dir)
        password = 'ELLO'
        store.insert_password('hello.com', password)

    def test_init(self):
        init_dir = tempfile.mkdtemp()
        PasswordStore.init(
            '5C5833E3',
            path=os.path.join(init_dir, '.password-store')
        )

        self.assertTrue(
            os.path.isdir(os.path.join(init_dir, '.password-store'))
        )

        self.assertTrue(
            os.path.isfile(
                os.path.join(init_dir, '.password-store', '.gpg-id')
            )
        )

        self.assertEqual(
            open(
                os.path.join(init_dir, '.password-store', '.gpg-id'),
                'r'
            ).read(),
            '5C5833E3\n'
        )

        shutil.rmtree(init_dir)

    def test_init_clone(self):
        origin_dir = tempfile.mkdtemp()
        destination_dir = tempfile.mkdtemp()

        subprocess.Popen(
            [
                'git',
                '--git-dir=%s' % os.path.join(origin_dir, '.git'),
                '--work-tree=%s' % origin_dir,
                'init',
                origin_dir
            ],
            shell=False
        ).wait()

        open(os.path.join(origin_dir, 'test_git_init_clone.gpg'), 'a').close()

        subprocess.Popen(
            [
                'git',
                '--git-dir=%s' % os.path.join(origin_dir, '.git'),
                '--work-tree=%s' % origin_dir,
                'add', 'test_git_init_clone.gpg',
            ]
        ).wait()

        subprocess.Popen(
            [
                'git',
                '--git-dir=%s' % os.path.join(origin_dir, '.git'),
                '--work-tree=%s' % origin_dir,
                'commit',
                '-m', '"testcommit"',
            ]
        ).wait()

        # Init
        PasswordStore.init(
            path=destination_dir,
            clone_url=origin_dir,
            gpg_id='3CCC3A3A'
        )

        # The key should be imported
        self.assertTrue(
            os.path.isfile(
                os.path.join(destination_dir, 'test_git_init_clone.gpg')
            )
        )

        # The gpg-id file should be created
        self.assertTrue(
            os.path.isfile(
                os.path.join(destination_dir, '.gpg-id')
            )
        )

        shutil.rmtree(origin_dir)
        shutil.rmtree(destination_dir)

    def test_generate_password(self):
        only_letters = PasswordStore.generate_password(
            digits=False,
            symbols=False
        )

        self.assertTrue(only_letters.isalpha())

        alphanum = PasswordStore.generate_password(digits=True, symbols=False)
        self.assertTrue(alphanum.isalnum())
        for char in alphanum:
            self.assertTrue(char not in string.punctuation)

        length_100 = PasswordStore.generate_password(length=100)
        self.assertEqual(len(length_100), 100)
