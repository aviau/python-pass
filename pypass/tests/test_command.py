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
import subprocess
import tempfile
import unittest

import click.testing

import pypass.command
import pypass.tests
from pypass.passwordstore import PasswordStore


class TestCommand(unittest.TestCase):

    def run_cli(self, args, input=None, expect_failure=False):
        args = ['--PASSWORD_STORE_DIR', self.dir] + list(args)
        runner = click.testing.CliRunner()
        result = runner.invoke(pypass.command.main, args, input=input)
        if result.exit_code != 0 and not expect_failure:
            if result.exception is not None:
                raise result.exception
            else:
                raise Exception(
                    'Invoking "pypass {}" failed'.format(' '.join(args)))
        return result

    def assertLastCommitMessage(self, text):
        git_log = subprocess.Popen(
            [
                'git',
                '--git-dir=%s' % os.path.join(self.dir, '.git'),
                '--work-tree=%s' % self.dir,
                'log', '-1', '--pretty=%B'
            ],
            shell=False,
            stdout=subprocess.PIPE
        )
        git_log.wait()
        self.assertEqual(git_log.stdout.read().decode(), text + '\n\n')

    def setUp(self):
        self.dir = tempfile.mkdtemp()

        # .gpg_id file
        with open(os.path.join(self.dir, '.gpg-id'), 'w') as gpg_id_file:
            gpg_id_file.write('5C5833E3')

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_init(self):
        init_dir = tempfile.mkdtemp()
        init_result = self.run_cli(
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
            '5C5833E3\n'
        )

        self.assertEqual(
            init_result.output,
            'Password store initialized for 5C5833E3.\n'
        )

        shutil.rmtree(init_dir)

    def test_insert(self):
        # Multiline input should end at EOF
        self.run_cli(['insert', '-m', 'test.com'], input='first\nsecond\n')

        store = PasswordStore(self.dir)
        content = store.get_decrypted_password('test.com')
        self.assertEqual(content, 'first\nsecond\n')

        # Echo the password and ask for it only once
        insert2 = self.run_cli(['insert', '-e', 'test2.com'], input='oneLine')

        self.assertEqual(
            insert2.output,
            'Enter password for test2.com: oneLine\n'
        )

        content2 = store.get_decrypted_password('test2.com')
        self.assertEqual(content2, 'oneLine')

        # Mismatching inputs should cause abort
        insert3 = self.run_cli(
            ['insert', 'test3.com'],
            input='aWildPassword\nDoesntMatch',
            expect_failure=True
        )
        self.assertNotEqual(insert3.exit_code, 0)

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

    def test_show_non_existing_password(self):
        # Show the password for test.com
        show_result = self.run_cli(
            ['show', 'test.com'],
            expect_failure=True
        )

        self.assertEqual(show_result.output,
                         'Error: test.com is not in the password store.\n')

    # Can't get xclip to work in Travis.
    @pypass.tests.skipIfTravis
    def test_show_clip(self):
        store = PasswordStore(self.dir)
        store.insert_password('clip_test', 'clipme999\nbutnotthisnewline\nfff')

        show_result = self.run_cli(['show', '-c', 'clip_test'])

        self.assertEqual(
            show_result.output,
            'Copied clip_test to clipboard.\n'
        )

        # Check if the password is in the clipoard
        xclip = subprocess.Popen(
            ['xclip', '-o', '-selection', 'clipboard'],
            stdout=subprocess.PIPE)
        xclip.wait()
        self.assertEqual(xclip.stdout.read().decode('utf8'), 'clipme999')

    def test_edit(self):
        store = PasswordStore(self.dir)
        store.insert_password('test.com', 'editme')

        mock_editor = os.path.join(os.path.dirname(__file__), 'mock_editor.py')
        self.run_cli(['--EDITOR', mock_editor, 'edit', 'test.com'])

        edited_content = store.get_decrypted_password('test.com')
        self.assertEqual(edited_content, 'edited')

    def test_edit_not_exist(self):
        edit_result = self.run_cli(
            ['edit', 'woijewoifj.ccc']
        )
        self.assertEqual(
            edit_result.output,
            'woijewoifj.ccc is not in the password store.\n'
        )

    def test_ls(self):
        # Create three dummy files
        open(os.path.join(self.dir, 'linux.ca.gpg'), 'a').close()
        open(os.path.join(self.dir, 'passwordstore.org.gpg'), 'a').close()
        open(os.path.join(self.dir, 'test.com.gpg'), 'a').close()

        ls_result = self.run_cli(['ls'])

        expected_regex = \
            r'Password Store\s.*linux.ca\s.*passwordstore.org\s.*test.com'

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
        rm_result = self.run_cli(['rm', 'test.com'], input='y\n')
        self.assertFalse(os.path.isfile(dummy_file_path))
        self.assertIsNotNone(
            re.match("Really remove .*test.com.gpg?", rm_result.output)
        )

    def test_rm_dont_exist(self):
        result = self.run_cli(['rm', 'test.com'])
        self.assertEqual(
            result.output,
            'Error: test.com is not in the password store.\n'
        )

    def test_rm_recursive(self):
        folder_path = os.path.join(self.dir, 'test_folder')
        os.mkdir(folder_path)
        self.assertTrue(os.path.isdir(folder_path))

        # Create three dummy files
        open(os.path.join(folder_path, 'linux.ca.gpg'), 'a').close()
        open(os.path.join(folder_path, 'passwordstore.org.gpg'), 'a').close()
        open(os.path.join(folder_path, 'test.com.gpg'), 'a').close()

        rm_result = self.run_cli(['rm', '-r', 'test_folder'], input='y\n')

        self.assertFalse(os.path.isdir(folder_path))
        self.assertIsNotNone(
            re.match("Recursively remove .*test_folder?", rm_result.output)
        )

    def test_mv_file(self):
        old_file_path = os.path.join(self.dir, 'move_me.gpg')
        open(old_file_path, 'a').close()

        self.assertTrue(os.path.isfile(old_file_path))

        self.run_cli(['mv', 'move_me', 'i_moved'])

        self.assertFalse(os.path.isfile(old_file_path))
        self.assertTrue(os.path.isfile(os.path.join(self.dir, 'i_moved.gpg')))

    def test_mv_folder(self):
        folder_path = os.path.join(self.dir, 'test_folder')
        os.mkdir(folder_path)
        self.assertTrue(os.path.isdir(folder_path))

        # Create three dummy files
        open(os.path.join(folder_path, 'linux.ca.gpg'), 'a').close()
        open(os.path.join(folder_path, 'passwordstore.org.gpg'), 'a').close()
        open(os.path.join(folder_path, 'test.com.gpg'), 'a').close()

        self.run_cli(['mv', 'test_folder', 'moved_folder'])

        self.assertFalse(os.path.isdir(folder_path))
        self.assertTrue(os.path.isdir(os.path.join(self.dir, 'moved_folder')))

    def test_mv_error(self):
        mv_result = self.run_cli(['mv', 'test_folder', 'moved_folder'])
        self.assertEqual(
            mv_result.output,
            'Error: test_folder is not in the password store\n'
        )

    def test_cp_file(self):
        old_file_path = os.path.join(self.dir, 'copy_me.gpg')
        open(old_file_path, 'a').close()

        self.assertTrue(os.path.isfile(old_file_path))

        self.run_cli(['cp', 'copy_me', 'i_was_copied'])

        self.assertTrue(os.path.isfile(old_file_path))
        self.assertTrue(
            os.path.isfile(os.path.join(self.dir, 'i_was_copied.gpg'))
        )

    def test_cp_folder(self):
        folder_path = os.path.join(self.dir, 'test_folder')
        os.mkdir(folder_path)
        self.assertTrue(os.path.isdir(folder_path))

        # Create three dummy files
        open(os.path.join(folder_path, 'linux.ca.gpg'), 'a').close()
        open(os.path.join(folder_path, 'passwordstore.org.gpg'), 'a').close()
        open(os.path.join(folder_path, 'test.com.gpg'), 'a').close()

        self.run_cli(['cp', 'test_folder', 'copied_folder'])

        self.assertTrue(os.path.isdir(folder_path))
        self.assertTrue(os.path.isdir(os.path.join(self.dir, 'copied_folder')))

    def test_cp_error(self):
        mv_result = self.run_cli(['cp', 'test_folder', 'moved_folder'])
        self.assertEqual(
            mv_result.output,
            'Error: test_folder is not in the password store\n'
        )

    def test_find(self):
        # Create dummy files
        open(os.path.join(self.dir, 'linux.ca.gpg'), 'a').close()
        open(os.path.join(self.dir, 'passwordstore.org.gpg'), 'a').close()
        open(os.path.join(self.dir, 'test.com.gpg'), 'a').close()
        open(os.path.join(self.dir, 'vv.com.gpg'), 'a').close()
        open(os.path.join(self.dir, 'zz.com.gpg'), 'a').close()

        find_result = self.run_cli(['find', 'pass', 'vv'])

        expected_regex = \
            r'Search\sTerms:\spass,vv\s.*passwordstore.org\s.*vv.com'

        self.assertIsNotNone(re.search(expected_regex, find_result.output))

    def test_grep(self):
        store = PasswordStore(self.dir)
        store.insert_password('grep_test.com', 'GREPME')

        grep_result = self.run_cli(['grep', 'GREPME'])
        self.assertEqual(
            grep_result.output,
            'grep_test.com:\nGREPME\n'
        )

    def test_git_init(self):
        self.run_cli(['git', 'init'])

        # git init should add a .gitattributes file
        self.assertEqual(
            open(os.path.join(self.dir, '.gitattributes'), 'r').read(),
            '*.gpg diff=gpg\n'
        )

        # git init should set diff.gpg.binary to True
        diff_gpg_binary = subprocess.Popen(
            [
                'git',
                '--git-dir=%s' % os.path.join(self.dir, '.git'),
                '--work-tree=%s' % self.dir,
                'config',
                '--local',
                'diff.gpg.binary'
            ],
            shell=False,
            stdout=subprocess.PIPE
        )
        diff_gpg_binary.wait()
        self.assertEqual(diff_gpg_binary.stdout.read().decode(), 'true\n')

        # git init should set diff.gpg.textconv to 'gpg -d'
        gpg = subprocess.Popen(
            [
                'git',
                '--git-dir=%s' % os.path.join(self.dir, '.git'),
                '--work-tree=%s' % self.dir,
                'config',
                '--local',
                'diff.gpg.textconv'
            ],
            shell=False,
            stdout=subprocess.PIPE
        )
        gpg.wait()
        self.assertEqual(gpg.stdout.read().decode(), 'gpg -d\n')

    def test_git_init_insert_and_show(self):
        self.run_cli(['git', 'init'])

        self.run_cli(
            ['insert', 'test.com'],
            input='super_secret\nsuper_secret'
        )

        self.assertTrue(os.path.isfile(os.path.join(self.dir, 'test.com.gpg')))
        self.assertLastCommitMessage(
            'Add given password for test.com to store.'
        )

        show_result = self.run_cli(
            ['show', 'test.com'],
            input='super_secret\nsuper_secret'
        )
        self.assertEqual(show_result.output, 'super_secret\n')

    def test_git_forward_options(self):
        self.run_cli(['git', 'init'])
        self.run_cli(
            ['insert', 'test.com'],
            input='super_secret\nsuper_secret'
        )

        self.run_cli(['git', 'commit', '--amend', '-m', 'Modified message.'])
        self.assertLastCommitMessage('Modified message.')

    def test_init_clone(self):
        # Setup origin repo
        origin_dir = tempfile.mkdtemp()
        origin_git_dir = os.path.join(origin_dir, '.git')

        subprocess.Popen(
            [
                'git',
                '--git-dir=%s' % origin_git_dir,
                '--work-tree=%s' % origin_dir,
                'init',
                origin_dir
            ],
            shell=False
        ).wait()

        open(os.path.join(origin_dir, 'test_git_init_clone.gpg'), 'a').close()

        subprocess.call(
            [
                'git',
                '--git-dir=%s' % origin_git_dir,
                '--work-tree=%s' % origin_dir,
                'add', 'test_git_init_clone.gpg',
            ]
        )

        subprocess.call(
            [
                'git',
                '--git-dir=%s' % origin_git_dir,
                '--work-tree=%s' % origin_dir,
                'commit',
                '-m', '"testcommit"',
            ]
        )

        # Init
        self.run_cli(
            [
                'init',
                '--path', self.dir,
                '--clone', origin_dir,
                'TEST_GPG_ID'
            ]
        )

        # The key should be imported
        self.assertTrue(
            os.path.isfile(
                os.path.join(self.dir, 'test_git_init_clone.gpg')
            )
        )

        # The gpg-id file should be created
        self.assertTrue(
            os.path.isfile(
                os.path.join(self.dir, '.gpg-id')
            )
        )

    def test_generate_no_symbols(self):
        generate = self.run_cli(['generate', '-n', 'test.com'])
        password = generate.output.partition('\n')[2].strip()
        self.assertIsNotNone(re.match('[a-zA-Z0-9]{25}$', password))

        store = PasswordStore(self.dir)
        decoded = store.get_decrypted_password('test.com')
        self.assertEqual(decoded, password)

    def test_generate_in_place(self):
        self.run_cli(['git', 'init'])
        store = PasswordStore(self.dir)

        generate = self.run_cli(
            ['generate', '-i', 'in-place.com'],
            expect_failure=True
        )
        self.assertNotEqual(generate.exit_code, 0)

        store.insert_password('in-place.com', 'first\nsecond')
        self.run_cli(['generate', '-i', 'in-place.com', '10'])

        self.assertLastCommitMessage(
            'Replace generated password for in-place.com.'
        )

        new_content = store.get_decrypted_password('in-place.com')
        new_password, _, remainder = new_content.partition('\n')
        self.assertEqual(len(new_password), 10)
        self.assertEqual(remainder, 'second')

    @pypass.tests.skipIfTravis
    def test_generate_clip(self):
        generate = self.run_cli(['generate', '-c', 'clip.me'])

        self.assertEqual(generate.output, 'Copied clip.me to clipboard.\n')

        xclip = subprocess.Popen(
            ['xclip', '-o', '-selection', 'clipboard'],
            stdout=subprocess.PIPE
        )
        xclip.wait()
        self.assertEqual(len(xclip.stdout.read().decode().strip()), 25)
