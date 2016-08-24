#!/usr/bin/env python

from __future__ import print_function

from githooks import args

files = args.pre_commit()

print('\nFiles:', *files.files, sep='\n')
print('\nModified:', *files.modified, sep='\n')
print('\nAdded:', *files.added, sep='\n')
print('\nDeleted:', *files.deleted, sep='\n')
