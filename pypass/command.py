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


@click.group(invoke_without_command=True)
@click.option('--PASSWORD_STORE_DIR',
              envvar='PASSWORD_STORE_DIR',
              default=os.path.join(os.getenv("HOME"), ".password-store"),
              type=click.Path(file_okay=False, resolve_path=True))
@click.pass_context
def main(ctx, password_store_dir):
    config = {}
    config['password_store_dir'] = password_store_dir

    gpg_id_file = os.path.join(password_store_dir, '.gpg-id')
    if os.path.isfile(gpg_id_file):
        config['gpg-id'] = open(gpg_id_file, 'r').read()

    ctx.obj = config

    # By default, invoke ls
    if ctx.invoked_subcommand is None:
        ctx.invoke(ls)


@main.command()
@click.option('--path', '-p',
              type=click.Path(file_okay=False, resolve_path=True),
              default=os.path.join(os.getenv("HOME"), ".password-store"),
              help='Where to create the password store.')
@click.argument('gpg-id', type=click.STRING)
def init(path, gpg_id):
    # Create a folder at the path
    if not os.path.exists(path):
        os.makedirs(path)

    # Create .gpg_id and put the gpg id in it
    with open(os.path.join(path, '.gpg-id'), 'w') as gpg_id_file:
        gpg_id_file.write(gpg_id)


@main.command()
@click.argument('path', type=click.STRING)
@click.pass_obj
def insert(config, path):
    passfile_path = os.path.realpath(
        os.path.join(
            config['password_store_dir'],
            path + '.gpg'
        )
    )

    password = click.prompt(
        'Enter the password',
        type=str,
        confirmation_prompt=True
    )

    gpg = subprocess.Popen(
        [
            'gpg2',
            '-e',
            '-r', config['gpg-id'],
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


@main.command()
@click.argument('path', type=click.STRING)
@click.pass_obj
def show(config, path):
    passfile_path = os.path.realpath(
        os.path.join(
            config['password_store_dir'],
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
        click.echo(gpg.stdout.read())


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
            os.path.join(config['password_store_dir'], subfolder),
        ],
        shell=False,
        stdout=subprocess.PIPE
    )
    tree.wait()

    if tree.returncode == 0:
        click.echo(tree.stdout.read().decode('utf8').replace('.gpg', ''))


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
            config['password_store_dir'],
        ],
        shell=False,
        stdout=subprocess.PIPE
    )
    tree.wait()

    if tree.returncode == 0:
        click.echo(tree.stdout.read(), nl=False)


@main.command()
@click.option('--recursive', '-r', is_flag=True)
@click.argument('path', type=click.STRING)
@click.pass_obj
def rm(config, recursive, path):
    resolved_path = os.path.realpath(
        os.path.join(config['password_store_dir'], path)
    )

    if os.path.isdir(resolved_path) is False:
        resolved_path = os.path.join(
            config['password_store_dir'],
            path + '.gpg'
        )

    if os.path.exists(resolved_path):
        if recursive:
            shutil.rmtree(resolved_path)
        else:
            os.remove(resolved_path)
    else:
        click.echo("Error: %s is not in the password store" % path)


@main.command()
@click.argument('old_path', type=click.STRING)
@click.argument('new_path', type=click.STRING)
@click.pass_obj
def mv(config, old_path, new_path):
    resolved_old_path = os.path.realpath(
        os.path.join(config['password_store_dir'], old_path)
    )

    if os.path.isdir(resolved_old_path):
        shutil.move(
            resolved_old_path,
            os.path.realpath(
                os.path.join(config['password_store_dir'], new_path)
            )
        )
    else:
        resolved_old_path = os.path.realpath(
            os.path.join(config['password_store_dir'], old_path + '.gpg')
        )

        if os.path.isfile(resolved_old_path):
            shutil.move(
                resolved_old_path,
                os.path.realpath(
                    os.path.join(
                        config['password_store_dir'],
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
    os.environ['GIT_DIR'] = os.path.join(config['password_store_dir'], '.git')
    os.environ['GIT_WORK_TREE'] = config['password_store_dir']

    command_list = list(commands)

    git_result = subprocess.Popen(
        ['git'] + command_list,
        shell=False,
    )
    git_result.wait()


if __name__ == '__main__':
    main()
