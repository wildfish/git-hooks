import string

import sys

from mock import Mock
from random import choice
from unittest import TestCase

from hypothesis import given
from hypothesis.strategies import text, dictionaries, lists, integers

from githooks.cmd import Base


class BaseSubParserDestName(TestCase):
    def test_name_is_none___argument_is_stored_in_sub_command(self):
        cmd = Base()

        self.assertEqual('sub_command', cmd.sub_parser_dest_name)

    @given(text(min_size=1, max_size=10, alphabet=string.printable))
    def test_name_is_not_none___argument_is_stored_in_name_plus_sub_command(self, name):
        cmd = Base(name)

        self.assertEqual(name + '__sub_command', cmd.sub_parser_dest_name)


class BaseParseArgs(TestCase):
    @given(dictionaries(text(min_size=1, max_size=10, alphabet=string.ascii_letters), text(min_size=1, max_size=10, alphabet=string.ascii_letters), min_size=1, max_size=10))
    def test_command_has_args_set___args_are_stored_in_the_result(self, arg_vals):
        class Cmd(Base):
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
    def test_command_has_args_set___args_are_stored_in_the_result(self, sub_parser_names, command_name):
        class SubCmd(Base):
            pass

        class Cmd(Base):
            sub_commands = {
                n: SubCmd for n in sub_parser_names
            }

        selected = choice(sub_parser_names)
        sys.argv = ['foo', selected]

        cmd = Cmd(command_name)
        args = cmd.parse_args()

        self.assertEqual(selected, getattr(args, cmd.sub_parser_dest_name))


class BaseAction(TestCase):
    def test_action_is_not_implemented_by_command___not_implemented_ir_raised(self):
        self.assertRaises(NotImplementedError, Base().action, None)


class BaseRun(TestCase):
    @given(
        integers(min_value=0, max_value=10),
        dictionaries(text(min_size=1, max_size=10, alphabet=string.ascii_letters), text(min_size=1, max_size=10, alphabet=string.ascii_letters), min_size=1, max_size=10),
    )
    def test_command_has_no_sub_parser___action_from_command_is_called(self, action_res, args):
        action_mock = Mock(return_value=action_res)

        class Cmd(Base):
            def add_args(self, parser):
                for k in args.keys():
                    parser.add_argument(k)

            def action(self, args):
                return action_mock(args)

        sys.argv = ['foo'] + list(args.values())

        cmd = Cmd()
        res = cmd.run()

        self.assertEqual(res, action_res)
        action_mock.assert_called_once_with(cmd.parse_args())

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

        class SubCmd(Base):
            def action(self, args):
                return action_mock(args)

        class OtherSubCmd(Base):
            def action(self, args):
                return other_action_mock(args)

        class Cmd(Base):
            sub_commands = {
                n: (SubCmd if n == selected else OtherSubCmd) for n in sub_parser_names
            }

        sys.argv = ['foo', selected]

        cmd = Cmd(command_name)
        res = cmd.run()

        self.assertEqual(res, action_res)
        action_mock.assert_called_once_with(cmd.parse_args())
        other_action_mock.assert_not_called()
