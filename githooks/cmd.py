from __future__ import print_function

import hashlib
import logging
import stat
from argparse import ArgumentParser

import posixpath
import requests
import os
import shutil

from . import utils, repo
from .compat import ConfigParser, urlsplit, urljoin, FileExistsException


logger = logging.getLogger(__name__)


def get_input():  # pragma: no cover (this is always mocked out)
    return input()


class Base(object):
    """
    The base command object

    :var description: The brief description of the command
    :var sub_commands: A dictionary mapping names to sub commands. Each value should be a class inheriting from Base.
    """
    description = None
    sub_commands = {}

    def __init__(self, name=None):
        """
        Creates the command
        :param name: The name the command is registered to
        """
        self.name = name
        self._arg_parser = None

    @property
    def sub_parser_dest_name(self):
        """
        The name of the argument the name of the sub command will be stored in
        """
        if self.name:
            return u'{0}__sub_command'.format(self.name)
        return 'sub_command'

    @property
    def arg_parser(self):
        if not self._arg_parser:
            self._arg_parser = ArgumentParser(self.get_description())
            self.add_args(self._arg_parser)
            self.register_sub_commands(self._arg_parser)

        return self._arg_parser

    def parse_args(self):
        """
        Parses the command line arguments

        :return: The arguments taken from the command line
        """
        return self.arg_parser.parse_args()

    def add_args(self, parser):
        """
        Adds arguments to the argument parser. This is used to modify which arguments are processed by the command.

        For a full description of the argument parser see https://docs.python.org/3/library/argparse.html.

        :param parser: The argument parser object
        """
        pass

    def register_sub_commands(self, parser):
        """
        Add any sub commands to the argument parser.

        :param parser: The argument parser object
        """
        sub_commands = self.get_sub_commands()
        if sub_commands:
            sub_parsers = parser.add_subparsers(dest=self.sub_parser_dest_name)

            for name, cls in sub_commands.items():
                cmd = cls(name)

                sub_parser = sub_parsers.add_parser(name, help=cmd.get_description(), description=cmd.get_description())

                cmd.add_args(sub_parser)
                cmd.register_sub_commands(sub_parser)

    def get_sub_commands(self):
        """
        Gets a dictionary mapping names to sub commands. Values should be classes inheriting from Base.

        :return: The list of sub commands.
        """
        return self.sub_commands

    def get_description(self):
        """
        Gets the description of the command
        """
        return self.description

    def action(self, args):
        """
        Performs the action of the command.

        This should be implemented by sub classes.

        :param args: The arguments parsed from parse_args
        :return: The status code of the action (0 on success)
        """
        self.arg_parser.print_help()
        return 1

    def run(self):
        """
        Runs the command passing in the parsed arguments.

        :return: The status code of the action (0 on success)
        """
        args = self.parse_args()

        sub_command_name = getattr(args, self.sub_parser_dest_name, None)
        if sub_command_name:
            return self.get_sub_commands()[sub_command_name]().action(args)
        return self.action(args)


class Init(Base):
    description = 'Initialises the hooks repository'

    def add_args(self, parser):
        parser.add_argument('-y', '--overwrite', help='Silently overwrite existing hooks', action='store_true', dest='overwrite')
        parser.add_argument('-n', '--no-overwrite', help='Silently avoid overwriting existing hooks', action='store_true', dest='no_overwrite')

    def action(self, args):
        if not repo.get().heads:
            logger.error('The hook runner doesnt currently work for new repos. Perform an initial commit before initialising githooks (see: https://github.com/wildfish/git-hooks/issues/4)')
            return 1

        if args.overwrite and args.no_overwrite:
            logger.error('Both the overwrite and no overwrite flags were set')
            return 1

        init_dir = os.path.join(repo.repo_root(), '.git', 'hooks')

        for hook_name in utils.get_hook_names():
            src = os.path.join(utils.get_hook_script_dir(), hook_name)
            dst = os.path.join(init_dir, hook_name)

            if not args.overwrite and os.path.exists(dst):
                if args.no_overwrite:
                    continue

                logger.info(u'A "{0}" already exists for this repository. Do you want to continue? y/[N]'.format(hook_name))
                c = get_input()
                if not(c.lower() == 'y' or c.lower() == 'yes'):
                    continue

            shutil.copy(src, dst)

            st = os.stat(dst)
            os.chmod(dst, st.st_mode | stat.S_IEXEC)

            try:
                os.mkdir(dst + '.d')
            except FileExistsException:
                pass

        return 0


class Install(Base):
    description = 'Installs the selected hook'

    def __init__(self, *args, **kwargs):
        self._config = None
        super(Install, self).__init__(*args, **kwargs)

    def add_args(self, parser):
        parser.add_argument('hook_type', nargs='?', help='The hook type to install. If no hook is given the config from "githooks.cfg" or "setup.cfg" is used', default=None, choices=utils.get_hook_names())
        parser.add_argument('hooks', nargs='*', help='The names/urls for hooks to install')
        parser.add_argument('-u', '--upgrade', help='Flag if hooks should be upgraded with the remote version', action='store_true', dest='upgrade')
        parser.add_argument('-y', '--yes', help='Flag if all hooks should be installed without prompting', action='store_true', dest='yes')

    def action(self, args):
        if args.hook_type:
            self._install_hooks(args.hook_type, args.hooks, args.upgrade, args.yes)
        else:
            for hook_type, hooks in self.config.items():
                self._install_hooks(hook_type, hooks, args.upgrade, args.yes)

    def _name_from_uri(self, uri):
        path = urlsplit(uri).path
        return posixpath.basename(path)

    def _install_hooks(self, hook_name, hooks, upgrade, install_all=False):
        type_repo = repo.hook_type_directory(hook_name)

        for hook in hooks:
            name = self._name_from_uri(hook)
            uri = hook

            # check if we need to skip based on the hook alread existing
            if not upgrade and os.path.exists(os.path.join(type_repo, name)):
                logger.info(u'"{0}" is already installed, use "--upgrade" to upgrade the hook to the newest version.'.format(name))
                continue

            response = requests.get(uri)

            # print file content so that it can be checked before installing
            if not install_all:
                logger.info('## Installing {} from {}'.format(name, uri))

                for line in response.content.decode().split('\n'):
                    logger.info(line)

                if not input('Continue? [y/N]: ').lower() in ['y', 'yes']:
                    logger.info('Not installing {} from {}'.format(name, uri))
                    continue

            # save the hook
            logger.info('Installing {} from {}'.format(name, uri))
            dst = os.path.join(type_repo, name)
            with open(dst, 'wb') as f:
                f.write(response.content)

            st = os.stat(dst)
            os.chmod(dst, st.st_mode | stat.S_IEXEC)

    @property
    def config(self):
        if self._config is None:  # pragma: no cover (dont need to cover the caching behaviour)
            parser = ConfigParser()

            if os.path.exists(os.path.join(repo.repo_root(), 'git-hooks.cfg')):
                parser.read(os.path.join(repo.repo_root(), 'git-hooks.cfg'))
                self._config = dict(
                    (k, v.split('\n')) for k, v in parser.items('install')
                )
            elif os.path.exists(os.path.join(repo.repo_root(), 'setup.cfg')):
                parser.read(os.path.join(repo.repo_root(), 'setup.cfg'))
                self._config = dict(
                    (k, v.split('\n')) for k, v in parser.items('git-hooks.install')
                )

        return self._config


class Uninstall(Base):
    def add_args(self, parser):
        parser.add_argument('hook_type', nargs='?', help='The hook type to uninstall.', choices=utils.get_hook_names())
        parser.add_argument('hooks', nargs='*', help='The names for hooks to uninstall')

    def action(self, args):
        type_dir = repo.hook_type_directory(args.hook_type)

        for hook in args.hooks:
            hook_path = os.path.join(type_dir, hook)

            if os.path.exists(hook_path):
                os.remove(hook_path)
            else:
                logger.info('{} hook called "{}" could not be found. SKIPPING.'.format(args.hook_type, hook))


class Hooks(Base):
    description = 'Manages your commit hooks for you!'
    sub_commands = {
        'init': Init,
        'install': Install,
        'uninstall': Uninstall,
    }
