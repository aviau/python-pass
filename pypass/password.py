#
#    Copyright (C) 2014 Alexandre Viau <alexandre@alexandreviau.net>
#    Copyright (C) 2020 Peter Rabi <peter.rabi@gmail.com>
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

import re

from .entry_type import EntryType


class Password:
    """Password is a decoded Password Store entry.

    It has two main `str` attributes:

    * `content`, which is the complete decoded text of the entry, and

    * `password`, which is either

      * the string following "pass: " or "password: " until \\n or EOF, or

      * the first line (without \\n).

    Content of specific `EntryType` can be retrieved by using
    `password_object[EntryType.enum_member]` syntax.
    """

    def __init__(self, content):
        self.content = content
        pw = re.search('(?:password|pass): (.+)', content)
        if pw is not None:
            self.password = pw.group(1)
        else:  # If there is no match, password is the first line
            self.password = content.partition('\n')[0]

    def __getitem__(self, key):
        """Get the value from a "key: value" formatted line.

        :param key: The key, that is an `EntryType` enum member.
        :returns: The `str` value corresponding to the given `key`.
                  `None`, if the `key` wasn't found.
        """
        if not isinstance(key, EntryType):
            raise TypeError(
                'Password objects can only retrieve EntryType values.'
            )
        if key is EntryType.password:
            return self.password
        elif key is EntryType.username:
            usr = re.search('(?:username|user|login): (.+)', self.content)
            if usr is not None:
                return usr.group(1)
        elif key is EntryType.hostname:
            hostname = re.search('(?:host|hostname): (.+)', self.content)
            if hostname is not None:
                return hostname.group(1)
