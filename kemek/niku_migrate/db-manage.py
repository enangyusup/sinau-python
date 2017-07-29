#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sys import argv

from dbreset import create, reset
from dbmigrate import migrate


if __name__ == '__main__':
    if len(argv) == 1:
        print 'males ah..'
    elif argv[1] == 'migrate':
        migrate()
    elif argv[1] == 'reset':
        reset()
    elif argv[1] == 'create':
        create()
    else:
        print 'apaan tuh!'
