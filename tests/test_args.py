import string
import sys

from githooks.args import pre_commit
from hypothesis import given
from hypothesis.strategies import text, lists
from unittest2 import TestCase


class ArgsPreCommit(TestCase):
    @given(
        lists(text(min_size=1, max_size=10, alphabet=string.ascii_letters), max_size=10),
        lists(text(min_size=1, max_size=10, alphabet=string.ascii_letters), max_size=10),
        lists(text(min_size=1, max_size=10, alphabet=string.ascii_letters), max_size=10),
        lists(text(min_size=1, max_size=10, alphabet=string.ascii_letters), max_size=10),
    )
    def test_args_have_correct_positional_added_modified_and_deleted(self, pos, added, modified, deleted):
        sys.argv = ['foo'] + pos + ['--added-files'] + added + ['--modified-files'] + modified + ['--deleted-files'] + deleted

        args = pre_commit()

        self.assertListEqual(pos, args.files)
        self.assertListEqual(added, args.added)
        self.assertListEqual(modified, args.modified)
        self.assertListEqual(deleted, args.deleted)
