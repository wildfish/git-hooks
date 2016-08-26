from random import randint

from hypothesis import example
from unittest2 import TestCase

from hypothesis import given
from hypothesis.strategies import lists, text, dictionaries
from mock import patch, Mock

from githooks import runners, finders


class FakeHookFinder(finders.HookFinder):
    def __init__(self, paths=None):
        self.paths = paths
        super(FakeHookFinder, self).__init__('fake-hook')

    def __iter__(self):
        for p in self.paths:
            yield p


class FakeRunner(runners.HookRunner):
    def __init__(self, process_args, process_kwargs, finder):
        self.process_args = process_args
        self.process_kwargs = process_kwargs
        self.finder = finder
        super(FakeRunner, self).__init__()

    def get_process_args(self, *args):
        return super(FakeRunner, self).get_process_args(*self.process_args)

    def get_process_kwargs(self, *args):
        return super(FakeRunner, self).get_process_kwargs(**self.process_kwargs)

    def get_finder(self):
        return self.finder


class HookRunnerRun(TestCase):
    @given(
        lists(text(min_size=1, max_size=10), max_size=10),
        dictionaries(text(min_size=1, max_size=10), text(min_size=0, max_size=10), max_size=10),
        lists(text(min_size=1, max_size=10), min_size=1, max_size=10),
    )
    @example([], {}, ['foo'])
    def test_hook_runner_is_ran___subprocess_is_called_for_each_hook_with_the_correct_args(self, process_args, process_kwargs, found_hooks):
        with patch('githooks.runners.subprocess') as subprocess_mock:
            expected_args = list(process_args)
            for k, v in sorted(process_kwargs.items()):
                if v:
                    expected_args.append(k)
                    expected_args.extend(v)

            runner = FakeRunner(process_args, process_kwargs, FakeHookFinder(found_hooks))

            return_values = [randint(0, 10) for i in found_hooks]
            subprocess_mock.call = Mock(side_effect=return_values)

            res = runner.run()

            self.assertEqual(len(found_hooks), subprocess_mock.call.call_count)
            self.assertEqual(sum(return_values), res)

            for p in found_hooks:
                subprocess_mock.call.assert_any_call([p] + expected_args)


class HookRunnerGetFinder(TestCase):
    def test_correct_finder_is_returned(self):
        class Cls(object):
            pass

        class Runner(runners.HookRunner):
            finder_class = Cls

        finder = Runner().get_finder()

        self.assertIsInstance(finder, Cls)


class PreCommitHookRunnerFinderClass(TestCase):
    def test_finder_class_is_pre_commit_hook_finder(self):
        self.assertEqual(finders.PreCommitHookFinder, runners.PreCommitHookRunner.finder_class)


class PreCommitHookRunnerGetProcessKwargs(TestCase):
    def test_result_contains_added_modified_and_deleted(self):
        with patch('githooks.repo.added_files', Mock(return_value=[])):
            with patch('githooks.repo.modified_files', Mock(return_value=[])):
                with patch('githooks.repo.deleted_files', Mock(return_value=[])):

                    kwargs = runners.PreCommitHookRunner().get_process_kwargs()

                    self.assertEqual(3, len(kwargs))
                    self.assertIn('--added-files', kwargs)
                    self.assertIn('--modified-files', kwargs)
                    self.assertIn('--deleted-files', kwargs)

    @given(lists(text(min_size=1, max_size=10), max_size=10))
    def test_result_contains_the_added_files(self, added_files):
        with patch('githooks.repo.added_files', Mock(return_value=added_files)):
            with patch('githooks.repo.modified_files', Mock(return_value=[])):
                with patch('githooks.repo.deleted_files', Mock(return_value=[])):

                    kwargs = runners.PreCommitHookRunner().get_process_kwargs()

                    self.assertEqual(added_files, kwargs['--added-files'])

    @given(lists(text(min_size=1, max_size=10), max_size=10))
    def test_result_contains_the_modified_files(self, modified_files):
        with patch('githooks.repo.added_files', Mock(return_value=[])):
            with patch('githooks.repo.modified_files', Mock(return_value=modified_files)):
                with patch('githooks.repo.deleted_files', Mock(return_value=[])):

                    kwargs = runners.PreCommitHookRunner().get_process_kwargs()

                    self.assertEqual(modified_files, kwargs['--modified-files'])

    @given(lists(text(min_size=1, max_size=10), max_size=10))
    def test_result_contains_the_deleted_files(self, deleted_files):
        with patch('githooks.repo.added_files', Mock(return_value=[])):
            with patch('githooks.repo.modified_files', Mock(return_value=[])):
                with patch('githooks.repo.deleted_files', Mock(return_value=deleted_files)):

                    kwargs = runners.PreCommitHookRunner().get_process_kwargs()

                    self.assertEqual(deleted_files, kwargs['--deleted-files'])


class PreCommitHookRunnerGetProcessArgs(TestCase):
    @given(
        lists(text(min_size=1, max_size=10), max_size=10),
        lists(text(min_size=1, max_size=10), max_size=10),
        lists(text(min_size=1, max_size=10), max_size=10),
    )
    def test_result_contains_the_added_files(self, added, modified, deleted):
        with patch('githooks.repo.added_files', Mock(return_value=added)):
            with patch('githooks.repo.modified_files', Mock(return_value=modified)):
                with patch('githooks.repo.deleted_files', Mock(return_value=deleted)):

                    args = runners.PreCommitHookRunner().get_process_args()

                    self.assertSequenceEqual(added + modified, args)
