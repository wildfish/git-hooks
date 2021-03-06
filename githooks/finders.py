import glob

import os

from . import repo


class HookFinder(object):
    """
    Searches through the hooks directory and gives each present hook. This is designed to be iterated over to get the
    absolute paths of each installed hook.

    :var hook_type: The type of hook to search for (such as 'pre-commit')
    """
    def __init__(self, hook_type):
        self.hook_type = hook_type

    def __iter__(self):
        hook_glob = os.path.join(repo.hook_type_directory(self.hook_type), '*')

        for p in glob.glob(hook_glob):
            yield p


class PreCommitHookFinder(HookFinder):
    def __init__(self):
        super(PreCommitHookFinder, self).__init__('pre-commit')
