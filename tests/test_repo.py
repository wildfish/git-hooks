import string
from unittest2 import TestCase

import os
from hypothesis import given
from hypothesis.strategies import text, lists
from mock import patch, Mock

from githooks import repo


class FakeDiffObject(object):
    def __init__(self, a_path, b_path, new, deleted):
        self.a_path = a_path
        self.b_path = b_path
        self.new_file = new
        self.deleted_file = deleted


class RepoGet(TestCase):
    @patch('githooks.repo.git')
    def test_result_is_repo_created_from_the_parent_of_script_directory(self, git_mock):
        git_mock.Repo = Mock(return_value='git repo')

        repo_obj = repo.get()

        self.assertEqual('git repo', repo_obj)
        git_mock.Repo.assert_called_once_with(
            os.getcwd(),
            search_parent_directories=True,
        )


class RepoRepoRoot(TestCase):
    @patch('githooks.repo.get')
    def test_result_is_the_parent_directory_of_the_git_diretory(self, get_mock):
        git_dir = os.path.dirname(__file__)
        result = Mock()
        result.git_dir = git_dir

        get_mock.return_value = result

        self.assertEqual(os.path.dirname(git_dir), repo.repo_root())


class RepoUntrackedFiles(TestCase):
    @patch('githooks.repo.get')
    def test_result_is_untracked_files_from_the_repo_object(self, get_mock):
        git_dir = os.path.dirname(__file__)

        result = Mock()
        result.untracked_files = ['untracked files']
        result.git_dir = git_dir

        get_mock.return_value = result

        files = repo.untracked_files()

        self.assertListEqual([os.path.join(repo.repo_root(), 'untracked files')], files)


class RepoModifiedFiles(TestCase):
    @given(
        lists(text(min_size=1, max_size=10, alphabet=string.ascii_letters), max_size=10),
        lists(text(min_size=1, max_size=10, alphabet=string.ascii_letters), max_size=10),
        lists(text(min_size=1, max_size=10, alphabet=string.ascii_letters), max_size=10),
    )
    def test_result_is_the_absolute_paths_to_all_changed_but_not_new_or_deleted_files(self, mod, new, deleted):
        mod_diffs = [FakeDiffObject(f, f, False, False) for f in mod]
        new_diffs = [FakeDiffObject(None, f, True, False) for f in new]
        deleted_diffs = [FakeDiffObject(None, f, False, True) for f in deleted]

        with patch('githooks.repo.get') as get_mock:
            git_dir = os.path.dirname(__file__)

            result = Mock()
            result.head.commit.diff = Mock(return_value=mod_diffs + new_diffs + deleted_diffs)
            result.git_dir = git_dir

            get_mock.return_value = result

            files = repo.modified_files()

            self.assertEqual([os.path.join(repo.repo_root(), f) for f in mod], files)
            result.head.commit.diff.assert_called_once_with()


class RepoAddedFiles(TestCase):
    @given(
        lists(text(min_size=1, max_size=10, alphabet=string.ascii_letters), max_size=10),
        lists(text(min_size=1, max_size=10, alphabet=string.ascii_letters), max_size=10),
        lists(text(min_size=1, max_size=10, alphabet=string.ascii_letters), max_size=10),
    )
    def test_result_is_the_absolute_paths_to_all_new_but_not_modified_or_deleted_files(self, mod, new, deleted):
        mod_diffs = [FakeDiffObject(f, f, False, False) for f in mod]
        new_diffs = [FakeDiffObject(None, f, True, False) for f in new]
        deleted_diffs = [FakeDiffObject(None, f, False, True) for f in deleted]

        with patch('githooks.repo.get') as get_mock:
            git_dir = os.path.dirname(__file__)

            result = Mock()
            result.head.commit.diff = Mock(return_value=mod_diffs + new_diffs + deleted_diffs)
            result.git_dir = git_dir

            get_mock.return_value = result

            files = repo.added_files()

            self.assertEqual([os.path.join(repo.repo_root(), f) for f in new], files)
            result.head.commit.diff.assert_called_once_with()


class RepoDeletedFiles(TestCase):
    @given(
        lists(text(min_size=1, max_size=10, alphabet=string.ascii_letters), max_size=10),
        lists(text(min_size=1, max_size=10, alphabet=string.ascii_letters), max_size=10),
        lists(text(min_size=1, max_size=10, alphabet=string.ascii_letters), max_size=10),
    )
    def test_result_is_the_absolute_paths_to_all_deleted_but_not_new_or_modified_files(self, mod, new, deleted):
        mod_diffs = [FakeDiffObject(f, f, False, False) for f in mod]
        new_diffs = [FakeDiffObject(None, f, True, False) for f in new]
        deleted_diffs = [FakeDiffObject(None, f, False, True) for f in deleted]

        with patch('githooks.repo.get') as get_mock:
            git_dir = os.path.dirname(__file__)

            result = Mock()
            result.head.commit.diff = Mock(return_value=mod_diffs + new_diffs + deleted_diffs)
            result.git_dir = git_dir

            get_mock.return_value = result

            files = repo.deleted_files()

            self.assertEqual([os.path.join(repo.repo_root(), f) for f in deleted], files)
            result.head.commit.diff.assert_called_once_with()
