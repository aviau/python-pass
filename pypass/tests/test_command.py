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
import re
import shutil
import tempfile
import unittest

import click.testing

import pypass.command


class TestCommand(unittest.TestCase):

    def run_cli(self, args, input=None):
        args = ['--PASSWORD_STORE_DIR', self.dir] + list(args)
        runner = click.testing.CliRunner()
        result = runner.invoke(pypass.command.main, args, input=input)
        return result

    def setUp(self):
        self.dir = tempfile.mkdtemp()

        # .gpg_id file
        with open(os.path.join(self.dir, '.gpg-id'), 'w') as gpg_id_file:
            gpg_id_file.write('5C5833E3')

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_init(self):
        init_dir = tempfile.mkdtemp()
        self.run_cli(
            [
                'init',
                '-p', os.path.join(init_dir, '.password-store'),
                '5C5833E3'
            ]
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
            '5C5833E3'
        )
        shutil.rmtree(init_dir)

    def test_insert_and_show(self):
        # Insert a password for test.com
        self.run_cli(
            ['insert', 'test.com'],
            input='super_secret\nsuper_secret'
        )

        self.assertTrue(
            os.path.isfile(os.path.join(self.dir, 'test.com.gpg'))
        )

        # Show the password for test.com
        show_result = self.run_cli(
            ['show', 'test.com'],
            input='super_secret\nsuper_secret'
        )

        self.assertEqual(show_result.output, 'super_secret\n')

    def test_ls(self):
        # Create three dummy files
        open(os.path.join(self.dir, 'linux.ca.gpg'), 'a').close()
        open(os.path.join(self.dir, 'passwordstore.org.gpg'), 'a').close()
        open(os.path.join(self.dir, 'test.com.gpg'), 'a').close()

        ls_result = self.run_cli(['ls'])

        expected_regex = \
            ".*linux.ca.gpg\s.*passwordstore.org.gpg\s.*test.com.gpg"

        self.assertIsNotNone(re.search(expected_regex, ls_result.output))

        # By default, pypass should run the ls command
        ls_default_result = self.run_cli([])
        self.assertEqual(ls_result.output, ls_default_result.output)

    def test_rm(self):
        # Create one dummy file
        dummy_file_path = os.path.join(self.dir, 'test.com.gpg')

        with open(dummy_file_path, 'w') as dummy_file:
            dummy_file.write('test.com')

        self.assertTrue(os.path.isfile(dummy_file_path))
        self.run_cli(['rm', 'test.com'])
        self.assertFalse(os.path.isfile(dummy_file_path))

    def test_rm_dont_exist(self):
        result = self.run_cli(['rm', 'test.com'])
        self.assertEqual(
            result.output,
            'Error: test.com is not in the password store\n'
        )
