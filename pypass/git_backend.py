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

from abc import ABCMeta, abstractmethod


class GitBackend:
    __metaclass__ = ABCMeta
    """Generic Git backend, does nothing."""

    @abstractmethod
    def add(self, repo_path, files):
        pass

    @abstractmethod
    def clone(self, url, target):
        pass

    @abstractmethod
    def commit(self, repo_path, message=None):
        pass

    @abstractmethod
    def init(self, repo_path):
        pass


class DulwichGitBackend(GitBackend):
    def __init__(self):
        from os import path
        from dulwich import porcelain
        self.path = path
        self.porcelain = porcelain

    def add(self, repo_path, files):
        self.porcelain.add(
            repo_path,
            [self.path.join(repo_path, file_name) for file_name in files]
        )

    def clone(self, url, target):
        self.porcelain.clone(url, target=target)

    def commit(self, repo_path, message=None):
        self.porcelain.commit(repo_path, message=message)

    def init(self, repo_path):
        self.porcelain.init(repo_path)


class SubprocessGitBackend(GitBackend):
    def __init__(self):
        from os import path
        from subprocess import call, Popen
        self.path = path
        self.call = call
        self.Popen = Popen

        self.call(
            [
                'git',
                '--version'
            ]
        )

    def add(self, repo_path, files):
        self.Popen(
            [
                'git',
                '--git-dir=%s'.format(self.path.join(repo_path, '.git')),
                '--work-tree=%s'.format(repo_path),
                'add'
            ] + files,
        ).wait()

    def clone(self, url, target):
        self.init(target)
        self.Popen(
            [
                'git',
                '--git-dir=%s'.format(self.path.join(target, '.git')),
                '--work-tree=%s'.format(target),
                'remote',
                'add',
                'origin',
                url
            ],
            shell=False,
        )
        self.Popen(
            [
                'git',
                '--git-dir=%s'.format(self.path.join(target, '.git')),
                '--work-tree=%s'.format(target),
                'pull',
                'origin',
                'master'
            ],
            shell=False,
        )

    def commit(self, repo_path, message=None):
        if message:
            self.call(
                [
                    'git',
                    '--git-dir=%s'.format(self.ath.join(repo_path, '.git')),
                    '--work-tree=%s'.format(repo_path),
                    'commit',
                    '-m',
                    message
                ]
            )
        else:
            self.call(
                [
                    'git',
                    '--git-dir=%s'.format(self.path.join(repo_path, '.git')),
                    '--work-tree=%s'.format(repo_path),
                    'commit'
                ]
            )

    def init(self, repo_path):
        self.Popen(
            [
                'git',
                '--git-dir=%s'.format(self.path.join(repo_path, '.git')),
                '--work-tree=%s'.format(repo_path),
                'init',
                repo_path
            ],
            shell=False,
        ).wait()
