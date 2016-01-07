import string

import sys
import os
import responses
import shutil
import tempfile
from mock import Mock, patch
from random import choice
from unittest2 import TestCase

from hypothesis import given, assume
from hypothesis.strategies import text, dictionaries, lists, integers, sampled_from, fixed_dictionaries

from githooks import cmd, utils, repo
from githooks.compat import ConfigParser


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
            sub_commands = dict(
                (n, SubCmd) for n in sub_parser_names
            )

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
            sub_commands = dict(
                (n, (SubCmd if n == selected else OtherSubCmd)) for n in sub_parser_names
            )

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
        with patch('githooks.cmd.repo.repo_root', Mock(return_value=self.repo_dir)):
            with patch('githooks.cmd.get_input', Mock(return_value='yes')):
                with patch('githooks.cmd.logger') as log_mock:
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
        with patch('githooks.cmd.repo.repo_root', Mock(return_value=self.repo_dir)):
            with patch('githooks.cmd.get_input', Mock(return_value='no')):
                with patch('githooks.cmd.logger') as log_mock:
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


class CmdInstall(TestCase):
    def setUp(self):
        self.hook_names = utils.get_hook_names()

    def make_repo_dir(self):
        repo_dir = tempfile.mkdtemp()
        hooks_dir = os.path.join(repo_dir, '.git', 'hooks')
        os.makedirs(hooks_dir)
        return repo_dir

    @given(
        text(min_size=1, alphabet=string.ascii_letters),
        text(min_size=1, max_size=10, alphabet=string.ascii_letters),
        text(min_size=1, max_size=10, alphabet=string.ascii_letters),
        sampled_from(utils.get_hook_names())
    )
    @responses.activate
    def test_hook_is_not_yet_installed___hook_is_installed(self, content, url_front, file_name, hook_name):
        repo_dir = self.make_repo_dir()

        try:
            url = 'http://' + url_front + '/' + file_name

            with patch('githooks.cmd.repo.repo_root', Mock(return_value=repo_dir)), patch('githooks.repo.repo_root', Mock(return_value=repo_dir)):
                sys.argv = ['foo', 'init', '-y']
                cmd.Hooks().run()

                responses.add(
                    responses.GET,
                    url,
                    body=content,
                    status=200,
                )

                sys.argv = ['foo', 'install', hook_name, url]

                cmd.Hooks().run()

                with open(os.path.join(repo.hook_type_directory(hook_name), file_name)) as f:
                    self.assertEqual(content, f.read())
        finally:
            shutil.rmtree(repo_dir)

    @given(
        text(min_size=1, alphabet=string.ascii_letters),
        text(min_size=1, alphabet=string.ascii_letters),
        text(min_size=1, max_size=10, alphabet=string.ascii_letters),
        text(min_size=1, max_size=10, alphabet=string.ascii_letters),
        sampled_from(utils.get_hook_names())
    )
    @responses.activate
    def test_hook_is_yet_installed_upgrade_is_not_set___hook_is_not_installed(self, orig_content, new_content, url_front, file_name, hook_name):
        assume(new_content != orig_content)

        repo_dir = self.make_repo_dir()

        try:
            url = 'http://' + url_front + '/' + file_name

            with patch('githooks.cmd.repo.repo_root', Mock(return_value=repo_dir)), patch('githooks.repo.repo_root', Mock(return_value=repo_dir)):
                sys.argv = ['foo', 'init', '-y']
                cmd.Hooks().run()

                with open(os.path.join(repo.hook_type_directory(hook_name), file_name), 'w') as f:
                    f.write(orig_content)

                responses.add(
                    responses.GET,
                    url,
                    body=new_content,
                    status=200,
                )

                sys.argv = ['foo', 'install', hook_name, url]

                cmd.Hooks().run()

                with open(os.path.join(repo.hook_type_directory(hook_name), file_name)) as f:
                    self.assertEqual(orig_content, f.read())
        finally:
            shutil.rmtree(repo_dir)

    @given(
        text(min_size=1, alphabet=string.ascii_letters),
        text(min_size=1, alphabet=string.ascii_letters),
        text(min_size=1, max_size=10, alphabet=string.ascii_letters),
        text(min_size=1, max_size=10, alphabet=string.ascii_letters),
        sampled_from(utils.get_hook_names())
    )
    @responses.activate
    def test_hook_is_yet_installed_upgrade_is_set___hook_is_installed(self, orig_content, new_content, url_front, file_name, hook_name):
        assume(new_content != orig_content)

        repo_dir = self.make_repo_dir()

        try:
            url = 'http://' + url_front + '/' + file_name

            with patch('githooks.cmd.repo.repo_root', Mock(return_value=repo_dir)), patch('githooks.repo.repo_root', Mock(return_value=repo_dir)):
                sys.argv = ['foo', 'init', '-y']
                cmd.Hooks().run()

                with open(os.path.join(repo.hook_type_directory(hook_name), file_name), 'w') as f:
                    f.write(orig_content)

                responses.add(
                    responses.GET,
                    url,
                    body=new_content,
                    status=200,
                )

                sys.argv = ['foo', 'install', hook_name, url, '--upgrade']

                cmd.Hooks().run()

                with open(os.path.join(repo.hook_type_directory(hook_name), file_name)) as f:
                    self.assertEqual(new_content, f.read())
        finally:
            shutil.rmtree(repo_dir)

    @given(
        dictionaries(
            sampled_from(utils.get_hook_names()),
            lists(fixed_dictionaries({
                'content': text(min_size=1, alphabet=string.ascii_letters),
                'front': text(min_size=1, max_size=10, alphabet=string.ascii_letters),
                'filename': text(min_size=1, max_size=10, alphabet=string.ascii_letters),
            }), min_size=1, max_size=10, unique_by=lambda x: x['filename']),
            min_size=1,
            max_size=len(utils.get_hook_names())
        ),
        dictionaries(
            sampled_from(utils.get_hook_names()),
            lists(fixed_dictionaries({
                'content': text(min_size=1, alphabet=string.ascii_letters),
                'front': text(min_size=1, max_size=10, alphabet=string.ascii_letters),
                'filename': text(min_size=1, max_size=10, alphabet=string.ascii_letters),
            }), min_size=1, max_size=10, unique_by=lambda x: x['filename']),
            min_size=1,
            max_size=len(utils.get_hook_names())
        ),
    )
    @responses.activate
    def test_config_is_given___all_hooks_from_config_are_installed(self, hook_configs, setup_configs):
        repo_dir = self.make_repo_dir()

        config = ConfigParser()
        hook_type_setting = {}
        for hook_type, hooks in hook_configs.items():
            hook_type_setting.setdefault(hook_type, '')

            for hook in hooks:
                url = 'http://' + hook['front'] + '/' + hook['filename']
                hook_type_setting[hook_type] += url + '\n'

                responses.add(
                    responses.GET,
                    url,
                    body=hook['content'],
                    status=200,
                )

        config.add_section('install')
        for hook_type, value in hook_type_setting.items():
            config.set('install', hook_type, value)

        with open(os.path.join(repo_dir, 'git-hooks.cfg'), 'w') as f:
            config.write(f)

        setup_config = ConfigParser()
        hook_type_setting = {}
        for hook_type, hooks in setup_configs.items():
            hook_type_setting.setdefault(hook_type, '')

            for hook in hooks:
                url = 'http://' + hook['front'] + '/' + hook['filename']
                hook_type_setting[hook_type] += url + '\n'

                responses.add(
                    responses.GET,
                    url,
                    body=hook['content'],
                    status=200,
                )

        setup_config.add_section('git-hooks.install')
        for hook_type, value in hook_type_setting.items():
            setup_config.set('git-hooks.install', hook_type, value)

        with open(os.path.join(repo_dir, 'setup.cfg'), 'w') as f:
            setup_config.write(f)

        try:
            with patch('githooks.cmd.repo.repo_root', Mock(return_value=repo_dir)), patch('githooks.repo.repo_root', Mock(return_value=repo_dir)):
                sys.argv = ['foo', 'init', '-y']
                cmd.Hooks().run()

                sys.argv = ['foo', 'install']

                cmd.Hooks().run()

                for hook_type, hooks in hook_configs.items():
                    for hook in hooks:
                        self.assertTrue(os.path.exists(os.path.join(repo.hook_type_directory(hook_type), hook['filename'])))
        finally:
            shutil.rmtree(repo_dir)

    @given(
        dictionaries(
            sampled_from(utils.get_hook_names()),
            lists(fixed_dictionaries({
                'content': text(min_size=1, alphabet=string.ascii_letters),
                'front': text(min_size=1, max_size=10, alphabet=string.ascii_letters),
                'filename': text(min_size=1, max_size=10, alphabet=string.ascii_letters),
            }), min_size=1, max_size=10, unique_by=lambda x: x['filename']),
            min_size=1,
            max_size=len(utils.get_hook_names())
        ),
    )
    @responses.activate
    def test_setup_config_is_given___all_hooks_from_setup_config_are_installed(self, setup_configs):
        repo_dir = self.make_repo_dir()

        setup_config = ConfigParser()
        hook_type_setting = {}
        for hook_type, hooks in setup_configs.items():
            hook_type_setting.setdefault(hook_type, '')

            for hook in hooks:
                url = 'http://' + hook['front'] + '/' + hook['filename']
                hook_type_setting[hook_type] += url + '\n'

                responses.add(
                    responses.GET,
                    url,
                    body=hook['content'],
                    status=200,
                )

        setup_config.add_section('git-hooks.install')
        for hook_type, value in hook_type_setting.items():
            setup_config.set('git-hooks.install', hook_type, value)

        with open(os.path.join(repo_dir, 'setup.cfg'), 'w') as f:
            setup_config.write(f)

        try:
            with patch('githooks.cmd.repo.repo_root', Mock(return_value=repo_dir)), patch('githooks.repo.repo_root', Mock(return_value=repo_dir)):
                sys.argv = ['foo', 'init', '-y']
                cmd.Hooks().run()

                sys.argv = ['foo', 'install']

                cmd.Hooks().run()

                for hook_type, hooks in setup_configs.items():
                    for hook in hooks:
                        self.assertTrue(os.path.exists(os.path.join(repo.hook_type_directory(hook_type), hook['filename'])))
        finally:
            shutil.rmtree(repo_dir)
