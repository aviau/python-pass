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

from ..passwordstore import GPG_BIN

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
        # .gpg_id file in subfolder
        with open(os.path.join(email_folder_path, '.gpg-id'), 'w') as gpg_id_file:
            gpg_id_file.write('86B4789B')

        open(os.path.join(email_folder_path, 'email.com.gpg'), 'a').close()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_constructor(self):
        # Construct on properly initialized directory
        store = PasswordStore(self.dir)
        self.assertEqual(store._get_gpg_id(self.dir), '5C5833E3')
        self.assertEqual(store._get_gpg_id(os.path.join(self.dir, 'Email')), '86B4789B')
        self.assertFalse(store.uses_git)
        self.assertEqual(self.dir, store.path)

        # Fail gracefully on missing .gpg-id
        gpg_id_path = os.path.join(self.dir, '.gpg-id')
        os.remove(gpg_id_path)
        self.assertRaises(Exception, PasswordStore, self.dir)

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
            store.get_decrypted_password('hello.com')
        )

    def test_get_decrypted_password_specific_entry(self):
        store = PasswordStore(self.dir)
        password = 'ELLO'
        store.insert_password('hello.com', password)

        # When there is no 'password:' mention, the password is assumed to be
        # the first line.
        self.assertEqual(
            'ELLO',
            store.get_decrypted_password('hello.com', entry=EntryType.password)
        )

        store.insert_password('hello.com', 'sdfsdf\npassword: pwd')
        self.assertEqual(
            'pwd',
            store.get_decrypted_password('hello.com', entry=EntryType.password)
        )

        store.insert_password(
            'hello',
            'sdf\npassword: pwd\nusername: bob\nhost: salut.fr'
        )
        self.assertEqual(
            'bob',
            store.get_decrypted_password('hello', entry=EntryType.username)
        )
        self.assertEqual(
            'salut.fr',
            store.get_decrypted_password('hello', entry=EntryType.hostname)
        )

    def test_get_decrypted_password_only_password(self):
        store = PasswordStore(self.dir)
        password = 'ELLO'
        store.insert_password('hello.com', password)
        self.assertEqual(
            'ELLO',
            store.get_decrypted_password('hello.com')
        )

    def test_get_decrypted_password_deeply_nested(self):
        store = PasswordStore(self.dir)
        self.assertFalse(
            os.path.isdir(os.path.join(self.dir, 'A', 'B', 'C'))
        )
        store.insert_password('A/B/C/D/hello.com', 'Alice')
        store.insert_password('A/B/C/hello.com', 'Bob')
        self.assertEqual(
            'Alice',
            store.get_decrypted_password('A/B/C/D/hello.com')
        )
        self.assertEqual(
            'Bob',
            store.get_decrypted_password('A/B/C/hello.com')
        )
        self.assertTrue(
            os.path.isdir(os.path.join(self.dir, 'A', 'B', 'C', 'D'))
        )

    def test_get_decrypted_password_doesnt_exist(self):
        store = PasswordStore(self.dir)
        self.assertRaises(Exception, store.get_decrypted_password, 'nope.com')

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
        store = PasswordStore(self.dir)

        store.generate_password('letters.net', digits=False, symbols=False)
        only_letters = store.get_decrypted_password('letters.net')
        self.assertTrue(only_letters.isalpha())

        store.generate_password('alphanum.co.uk', digits=True, symbols=False)
        alphanum = store.get_decrypted_password('alphanum.co.uk')
        self.assertTrue(alphanum.isalnum())
        for char in alphanum:
            self.assertTrue(char not in string.punctuation)

        store.generate_password('hundred.org', length=100)
        length_100 = store.get_decrypted_password('hundred.org')
        self.assertEqual(len(length_100), 100)

    def test_generate_password_uses_correct_gpg_id(self):
        store = PasswordStore(self.dir)

        def get_gpg_ids_used(filename):
            gpg = subprocess.Popen(
                [
                    GPG_BIN,
                    '--list-packets',
                    os.path.join(self.dir, filename)
                ],
                shell=False,
                stdout=subprocess.PIPE
            )
            gpg.wait()
            pubkeys = []
            for line in gpg.stdout.readlines():
                if line.startswith(':pubkey'):
                    pubkeys.append(line.split()[-1])

            return pubkeys

        store.generate_password('should_use_main_key')
        pubkeys = get_gpg_ids_used('should_use_main_key.gpg')
        self.assertTrue(len(pubkeys) == 1)
        self.assertEqual(pubkeys[0], '6C8110881C10BC07')

        store.generate_password('Email/should_use_secondary_key')
        pubkeys = get_gpg_ids_used(os.path.join('Email', 'should_use_secondary_key.gpg'))
        self.assertTrue(len(pubkeys) == 1)
        self.assertEqual(pubkeys[0], '4B52397C4C1C5D70')

    def test_generate_in_place(self):
        store = PasswordStore(self.dir)

        self.assertRaises(
            Exception,
            store.generate_password,
            'nope.org',
            first_line_only=True
        )

        store.insert_password('nope.org', 'pw\nremains intact')
        store.generate_password('nope.org', length=3, first_line_only=True)

        new_content = store.get_decrypted_password('nope.org')
        new_password, _, remainder = new_content.partition('\n')
        self.assertNotEqual(new_password, 'pw')
        self.assertEqual(remainder, 'remains intact')
