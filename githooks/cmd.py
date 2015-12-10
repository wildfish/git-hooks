from argparse import ArgumentParser


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

    @property
    def sub_parser_dest_name(self):
        """
        The name of the argument the name of the sub command will be stored in
        """
        if self.name:
            return '{}__sub_command'.format(self.name)
        return 'sub_command'

    def parse_args(self):
        """
        Parses the command line arguments

        :return: The arguments taken from the command line
        """
        parser = ArgumentParser(self.get_description())
        self.add_args(parser)
        self.register_sub_commands(parser)
        return parser.parse_args()

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
        raise NotImplementedError()

    def run(self):
        """
        Runs the command passing in the parsed arguments.

        :return: The status code of the action (0 on success)
        """
        args = self.parse_args()

        print(args)

        sub_command_name = getattr(args, self.sub_parser_dest_name, None)
        if sub_command_name:
            return self.get_sub_commands()[sub_command_name]().action(args)
        return self.action(args)
#
#
# class Init(Base):
#     description = 'Initialises the hooks repository'
#
#     def action(self, args):
#         print(args)
#
#
# class Hooks(Base):
#     description = 'Manages your commit hooks for you!'
#     sub_commands = {
#         'init': Init
#     }
#
