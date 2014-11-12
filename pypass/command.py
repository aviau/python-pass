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

import click
import os
import subprocess
import shutil
import tempfile

from pypass.passwordstore import PasswordStore


@click.group(invoke_without_command=True)
@click.option('--PASSWORD_STORE_DIR',
              envvar='PASSWORD_STORE_DIR',
              default=os.path.join(os.getenv("HOME"), ".password-store"),
              type=click.Path(file_okay=False, resolve_path=True))
@click.option('--PASSWORD_STORE_GIT',
              envvar='PASSWORD_STORE_GIT',
              type=click.Path(file_okay=False, resolve_path=True),
              default=None)
@click.option('--EDITOR',
              envvar='EDITOR',
              default='editor',
              type=click.STRING)
@click.pass_context
def main(ctx, password_store_dir, password_store_git, editor):

    # init does not need any of this.
    if ctx.invoked_subcommand == "init":
        return

    # Prepare the config file
    config = {
        'password_store': PasswordStore(
            path=password_store_dir,
            git_dir=password_store_git
        ),
        'editor': editor
    }

    ctx.obj = config

    # By default, invoke ls
    if ctx.invoked_subcommand is None:
        ctx.invoke(ls)


@main.command()
@click.option('--path', '-p',
              type=click.Path(file_okay=False, resolve_path=True),
              default=os.path.join(os.getenv("HOME"), ".password-store"),
              help='Where to create the password store.')
@click.option('--clone', '-c',
              type=click.STRING,
              help='Git url to clone')
@click.argument('gpg-id', type=click.STRING)
def init(path, clone, gpg_id):
    PasswordStore.init(gpg_id, path, clone_url=clone)
    click.echo("Password store initialized for %s." % gpg_id)


@main.command()
@click.option('--multiline', '-m', is_flag=True)
@click.argument('path', type=click.STRING)
@click.pass_obj
def insert(config, path, multiline):

    if multiline:
        with tempfile.NamedTemporaryFile() as temp_file:
            if subprocess.call([config['editor'], temp_file.name]) == 0:
                password = temp_file.read().strip()
    else:
        password = click.prompt(
            'Enter the password',
            type=str,
            confirmation_prompt=True
        )

    config['password_store'].insert_password(path, password)

    if config['password_store'].uses_git:
        config['password_store'].git_add_and_commit(
            path + '.gpg',
            message='Added %s to store' % path
        )


@main.command()
@click.argument('path', type=click.STRING)
@click.pass_obj
def show(config, path):
    click.echo(
        config['password_store'].get_decypted_password(path).strip(),
    )


@main.command()
@click.argument('subfolder', required=False, type=click.STRING, default='')
@click.pass_obj
def ls(config, subfolder):
    tree = subprocess.Popen(
        [
            'tree',
            '-C',
            '-l',
            '--noreport',
            os.path.join(config['password_store'].path, subfolder),
        ],
        shell=False,
        stdout=subprocess.PIPE
    )
    tree.wait()

    if tree.returncode == 0:
        output_without_gpg = \
            tree.stdout.read().decode('utf8').replace('.gpg', '')

        output_replaced_first_line =\
            "Password Store\n" + '\n'.join(output_without_gpg.split('\n')[1:])

        output_stripped = output_replaced_first_line.strip()

        click.echo(output_stripped)


@main.command()
@click.argument('search_terms', nargs=-1)
@click.pass_obj
def find(config, search_terms):
    click.echo("Search Terms: " + ','.join(search_terms))

    pattern = '*' + '*|*'.join(search_terms) + '*'

    tree = subprocess.Popen(
        [
            'tree',
            '-C',
            '-l',
            '--noreport',
            '-P', pattern,
            # '--prune', (tree>=1.5)
            # '--matchdirs', (tree>=1.7)
            # '--ignore-case', (tree>=1.7)
            config['password_store'].path,
        ],
        shell=False,
        stdout=subprocess.PIPE
    )
    tree.wait()

    if tree.returncode == 0:
        output_without_gpg = \
            tree.stdout.read().decode('utf8').replace('.gpg', '')

        output_without_first_line =\
            '\n'.join(output_without_gpg.split('\n')[1:]).strip()

        click.echo(output_without_first_line)


@main.command()
@click.option('--recursive', '-r', is_flag=True)
@click.argument('path', type=click.STRING)
@click.pass_obj
def rm(config, recursive, path):
    resolved_path = os.path.realpath(
        os.path.join(config['password_store'].path, path)
    )

    if os.path.isdir(resolved_path) is False:
        resolved_path = os.path.join(
            config['password_store'].path,
            path + '.gpg'
        )

    if os.path.exists(resolved_path):
        if recursive:
            click.confirm("Recursively remove %s?" % resolved_path, abort=True)
            shutil.rmtree(resolved_path)
        else:
            click.confirm("Really remove %s?" % resolved_path, abort=True)
            os.remove(resolved_path)
        click.echo("%s was removed from the store." % path)
    else:
        click.echo("Error: %s is not in the password store." % path)


@main.command()
@click.argument('old_path', type=click.STRING)
@click.argument('new_path', type=click.STRING)
@click.pass_obj
def cp(config, old_path, new_path):
    resolved_old_path = os.path.realpath(
        os.path.join(config['password_store'].path, old_path)
    )

    if os.path.isdir(resolved_old_path):
        shutil.copytree(
            resolved_old_path,
            os.path.realpath(
                os.path.join(config['password_store'].path, new_path)
            )
        )
    else:
        resolved_old_path = os.path.realpath(
            os.path.join(config['password_store'].path, old_path + '.gpg')
        )

        if os.path.isfile(resolved_old_path):
            shutil.copy(
                resolved_old_path,
                os.path.realpath(
                    os.path.join(
                        config['password_store'].path,
                        new_path + '.gpg'
                    )
                )
            )
        else:
            click.echo("Error: %s is not in the password store" % old_path)


@main.command()
@click.argument('old_path', type=click.STRING)
@click.argument('new_path', type=click.STRING)
@click.pass_obj
def mv(config, old_path, new_path):
    resolved_old_path = os.path.realpath(
        os.path.join(config['password_store'].path, old_path)
    )

    if os.path.isdir(resolved_old_path):
        shutil.move(
            resolved_old_path,
            os.path.realpath(
                os.path.join(config['password_store'].path, new_path)
            )
        )
    else:
        resolved_old_path = os.path.realpath(
            os.path.join(config['password_store'].path, old_path + '.gpg')
        )

        if os.path.isfile(resolved_old_path):
            shutil.move(
                resolved_old_path,
                os.path.realpath(
                    os.path.join(
                        config['password_store'].path,
                        new_path + '.gpg'
                    )
                )
            )
        else:
            click.echo("Error: %s is not in the password store" % old_path)


@main.command()
@click.argument('commands', nargs=-1)
@click.pass_obj
def git(config, commands):
    command_list = list(commands)

    if len(command_list) > 0 and command_list[0] == 'init':
        config['password_store'].git_init()
    else:
        subprocess.call(
            [
                'git',
                '--git-dir=%s' % config['password_store'].git_dir,
                '--work-tree=%s' % config['password_store'].path,
            ] + command_list,
            shell=False,
        )


if __name__ == '__main__':
    main()
