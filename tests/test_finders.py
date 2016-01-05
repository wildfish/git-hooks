from unittest import TestCase

import os
from hypothesis import given
from hypothesis.strategies import text, lists
from mock import patch, Mock

from githooks import finders, repo


class HookFinderTests(TestCase):
    @given(text(min_size=1, max_size=10), text(min_size=1, max_size=10), lists(text(min_size=1, max_size=10), min_size=1, max_size=10))
    def test_iterate_over_the_hook_finder___all_files_in_the_commit_hooks_directory_are_returned(self, hook_name, repo_dir, files):
        with patch('githooks.finders.glob') as glob_mock, patch('githooks.repo.repo_root', Mock(return_value=repo_dir)):
            glob_mock.glob = Mock(return_value=files)

            found = finders.HookFinder(hook_name)

            self.assertListEqual(files, list(found))
            glob_mock.glob.assert_called_once_with(os.path.join(repo_dir, '.git', 'hooks', hook_name + '.d', '*'))


class PreCommitHookFinderTest(TestCase):
    def test_is_instance_of_hook_finder_and_has_pre_commit_hook_type(self):
        finder = finders.PreCommitHookFinder()

        self.assertIsInstance(finder, finders.HookFinder)
        self.assertEqual('pre-commit', finder.hook_type)
