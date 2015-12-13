import string

import sys
import uuid

import os
import shutil
import tempfile
from mock import Mock, patch
from random import choice
from unittest import TestCase

from hypothesis import given
from hypothesis.strategies import text, dictionaries, lists, integers

from githooks import cmd, utils


class BaseSubParserDestName(TestCase):
    def test_name_is_none___argument_is_stored_in_sub_command(self):
        command = cmd.Base()

        self.assertEqual('sub_command', command.sub_parser_dest_name)

    @given(text(min_size=1, max_size=10, alphabet=string.printable))
    def test_name_is_not_none___argument_is_stored_in_name_plus_sub_command(self, name):
        command = cmd.Base(name)

        self.assertEqual(name + '__sub_command', command.sub_parser_dest_name)


class BaseParseArgs(TestCase):
    @given(dictionaries(text(min_size=1, max_size=10, alphabet=string.ascii_letters), text(min_size=1, max_size=10, alphabet=string.ascii_letters), min_size=1, max_size=10))
    def test_command_has_args_set___args_are_stored_in_the_result(self, arg_vals):
        class Cmd(cmd.Base):
            def add_args(self, parser):
                for k in arg_vals.keys():
                    parser.add_argument(k)

        sys.argv = ['foo'] + list(arg_vals.values())

        args = Cmd().parse_args()

        for k, v in arg_vals.items():
            self.assertEqual(v, getattr(args, k))

    @given(
        lists(text(min_size=1, max_size=10, alphabet=string.ascii_letters), min_size=1, max_size=10),
        text(min_size=1, max_size=10, alphabet=string.ascii_letters),
    )
    def test_command_has_sub_command_arg_set___sub_command_is_called(self, sub_parser_names, command_name):
        class SubCmd(cmd.Base):
            pass

        class Cmd(cmd.Base):
            sub_commands = {
                n: SubCmd for n in sub_parser_names
            }

        selected = choice(sub_parser_names)
        sys.argv = ['foo', selected]

        command = Cmd(command_name)
        args = command.parse_args()

        self.assertEqual(selected, getattr(args, command.sub_parser_dest_name))


class BaseAction(TestCase):
    def test_action_is_not_implemented_by_command___the_action_help_is_printed(self):
        command = cmd.Base()
        command.arg_parser.print_help = Mock()

        self.assertEqual(1, command.action(None))
        command.arg_parser.print_help.assert_called_once_with()


class BaseRun(TestCase):
    @given(
        integers(min_value=0, max_value=10),
        dictionaries(text(min_size=1, max_size=10, alphabet=string.ascii_letters), text(min_size=1, max_size=10, alphabet=string.ascii_letters), min_size=1, max_size=10),
    )
    def test_command_has_no_sub_parser___action_from_command_is_called(self, action_res, args):
        action_mock = Mock(return_value=action_res)

        class Cmd(cmd.Base):
            def add_args(self, parser):
                for k in args.keys():
                    parser.add_argument(k)

            def action(self, args):
                return action_mock(args)

        sys.argv = ['foo'] + list(args.values())

        command = Cmd()
        res = command.run()

        self.assertEqual(res, action_res)
        action_mock.assert_called_once_with(command.parse_args())

    @given(
        integers(min_value=0, max_value=10),
        integers(min_value=11, max_value=20),
        lists(text(min_size=1, max_size=10, alphabet=string.ascii_letters), min_size=1, max_size=10),
        text(min_size=1, max_size=10, alphabet=string.ascii_letters),
    )
    def test_command_has_no_sub___action_from_command_is_called(self, action_res, other_action_res, sub_parser_names, command_name):
        selected = choice(sub_parser_names)

        action_mock = Mock(return_value=action_res)
        other_action_mock = Mock(return_value=other_action_res)

        class SubCmd(cmd.Base):
            def action(self, args):
                return action_mock(args)

        class OtherSubCmd(cmd.Base):
            def action(self, args):
                return other_action_mock(args)

        class Cmd(cmd.Base):
            sub_commands = {
                n: (SubCmd if n == selected else OtherSubCmd) for n in sub_parser_names
            }

        sys.argv = ['foo', selected]

        command = Cmd(command_name)
        res = command.run()

        self.assertEqual(res, action_res)
        action_mock.assert_called_once_with(command.parse_args())
        other_action_mock.assert_not_called()


class CmdInit(TestCase):
    def setUp(self):
        self.repo_dir = tempfile.mkdtemp()
        self.hooks_dir = os.path.join(self.repo_dir, '.git', 'hooks')
        os.makedirs(self.hooks_dir)

        self.hook_names = utils.get_hook_names()

    def tearDown(self):
        shutil.rmtree(self.repo_dir)

    def test_user_has_no_preexisitng_hooks___hooks_are_initialised(self):
        with patch('githooks.cmd.repo.repo_root', Mock(return_value=self.repo_dir)):
            sys.argv = ['foo', 'init']

            cmd.Hooks().run()

            self.assertGreater(len(self.hook_names), 0)
            for name in self.hook_names:
                self.assertTrue(os.path.exists(os.path.join(self.hooks_dir, name)))
                self.assertTrue(os.path.exists(os.path.join(self.hooks_dir, name + '.d')))

    def test_user_has_preexisitng_hooks_user_responds_yes_to_all___all_are_overwritten(self):
        with patch('githooks.cmd.repo.repo_root', Mock(return_value=self.repo_dir)), \
                patch('githooks.cmd.input', Mock(return_value='yes')), \
                patch('githooks.cmd.logger') as log_mock:

            sys.argv = ['foo', 'init']

            for name in self.hook_names:
                with open(os.path.join(self.hooks_dir, name), 'w') as f:
                    f.write(name)

            cmd.Hooks().run()

            self.assertGreater(len(self.hook_names), 0)
            for name in self.hook_names:
                with open(os.path.join(self.hooks_dir, name)) as f, \
                        open(os.path.join(utils.get_hook_script_dir(), name)) as new:
                    self.assertEqual(new.read(), f.read())

                log_mock.info.assert_called_once_with('A "{}" already exists for this repository. Do you want to continue? y/[N]'.format(name))

    def test_user_has_preexisitng_hooks_user_responds_no_to_all___no_are_overwritten(self):
        with patch('githooks.cmd.repo.repo_root', Mock(return_value=self.repo_dir)), \
                patch('githooks.cmd.input', Mock(return_value='no')), \
                patch('githooks.cmd.logger') as log_mock:

            sys.argv = ['foo', 'init']

            for name in self.hook_names:
                with open(os.path.join(self.hooks_dir, name), 'w') as f:
                    f.write(name)

            cmd.Hooks().run()

            self.assertGreater(len(self.hook_names), 0)
            for name in self.hook_names:
                with open(os.path.join(self.hooks_dir, name)) as f:
                    self.assertEqual(name, f.read())

                log_mock.info.assert_called_once_with('A "{}" already exists for this repository. Do you want to continue? y/[N]'.format(name))

    def test_user_has_preexisitng_hooks_with_overwrite_flag___all_are_overwritten(self):
        with patch('githooks.cmd.repo.repo_root', Mock(return_value=self.repo_dir)), \
                patch('githooks.cmd.logger') as log_mock:

            sys.argv = ['foo', 'init', '-y']

            for name in self.hook_names:
                with open(os.path.join(self.hooks_dir, name), 'w') as f:
                    f.write(name)

            cmd.Hooks().run()

            self.assertGreater(len(self.hook_names), 0)
            for name in self.hook_names:
                with open(os.path.join(self.hooks_dir, name)) as f, \
                        open(os.path.join(utils.get_hook_script_dir(), name)) as new:
                    self.assertEqual(new.read(), f.read())

                log_mock.info.assert_not_called()

    def test_user_has_preexisitng_hooks_with_no_overwrite_flag___no_are_overwritten(self):
        with patch('githooks.cmd.repo.repo_root', Mock(return_value=self.repo_dir)), \
                patch('githooks.cmd.logger') as log_mock:

            sys.argv = ['foo', 'init', '-n']

            for name in self.hook_names:
                with open(os.path.join(self.hooks_dir, name), 'w') as f:
                    f.write(name)

            cmd.Hooks().run()

            self.assertGreater(len(self.hook_names), 0)
            for name in self.hook_names:
                with open(os.path.join(self.hooks_dir, name)) as f:
                    self.assertEqual(name, f.read())

                log_mock.info.assert_not_called()

    def test_one_of_the_hook_directories_already_exists___the_process_continues_as_normal(self):
        with patch('githooks.cmd.repo.repo_root', Mock(return_value=self.repo_dir)):
            sys.argv = ['foo', 'init']

            os.mkdir(os.path.join(self.hooks_dir, self.hook_names[0] + '.d'))
            cmd.Hooks().run()

            self.assertGreater(len(self.hook_names), 0)
            for name in self.hook_names:
                self.assertTrue(os.path.exists(os.path.join(self.hooks_dir, name)))
                self.assertTrue(os.path.exists(os.path.join(self.hooks_dir, name + '.d')))

    def test_both_the_overwrite_and_no_overrwrtie_flags_are_set___the_user_is_given_an_error_and_the_process_exits(self):
        with patch('githooks.cmd.repo.repo_root', Mock(return_value=self.repo_dir)), \
                patch('githooks.cmd.logger') as log_mock:
            sys.argv = ['foo', 'init', '-y', '-n']

            self.assertEqual(1, cmd.Hooks().run())

            self.assertGreater(len(self.hook_names), 0)
            for name in self.hook_names:
                self.assertFalse(os.path.exists(os.path.join(self.hooks_dir, name)))
                self.assertFalse(os.path.exists(os.path.join(self.hooks_dir, name + '.d')))

            log_mock.error.assert_called_once_with('Both the overwrite and no overwrite flags were set')
