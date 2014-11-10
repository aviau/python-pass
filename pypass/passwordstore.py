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


class PasswordStore(object):

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
        raise NotImplemented()
