#!/usr/bin/env python

#
#    Copyright (C) 2019 Peter Rabi <peter.rabi@gmail.com>
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

'''mock_editor.py is an editor simulator.

One command line argument is expected: a file path.
Upon invocation the file's content gets replaced with the plain text 'edited'.
'''

import sys

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('ERR: Unexpected number of arguments.\n\n{}'.format(__doc__))

    file_path = sys.argv[1]
    try:
        with open(file_path, 'w') as f:
            f.write('edited')
    except (IOError, OSError) as e:
        sys.exit('Couldn\'t edit {}\n{}'.format(file_path, e))
