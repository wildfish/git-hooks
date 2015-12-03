from random import randint
from unittest import TestCase

from hypothesis import given
from hypothesis.strategies import builds, lists, text, dictionaries
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
        dictionaries(text(min_size=1, max_size=10), text(min_size=1, max_size=10), max_size=10),
        lists(text(min_size=1, max_size=10), min_size=1, max_size=10),
    )
    def test_hook_runner_is_ran___subprocess_is_called_for_each_hook_with_the_correct_args(self, process_args, process_kwargs, found_hooks):
        with patch('githooks.runners.subprocess') as subprocess_mock:
            expected_args = list(process_args)
            for k_v in sorted(process_kwargs.items()):
                expected_args.extend(k_v)

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
