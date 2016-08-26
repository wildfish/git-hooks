import os
import shutil
import tempfile

import sys

from githooks import cmd
from mock import Mock, patch


class FakeRepoDir(object):
    def __init__(self):
        self.patches = []
        self.repo_dir = ''

    def __str__(self):
        return self.repo_dir

    def __enter__(self):
        self._make_repo_dir()

        self.patches = [
            patch('githooks.cmd.repo.repo_root', Mock(return_value=self.repo_dir)),
            patch('githooks.repo.repo_root', Mock(return_value=self.repo_dir)),
        ]

        for p in self.patches:
            p.__enter__()

        sys.argv = ['foo', 'init', '-y']
        cmd.Hooks().run()

        return self

    def __exit__(self, *args):
        shutil.rmtree(self.repo_dir)

        for p in reversed(self.patches):
            p.__exit__(*args)

    def _make_repo_dir(self):
        self.repo_dir = tempfile.mkdtemp()
        hooks_dir = os.path.join(self.repo_dir, '.git', 'hooks')
        os.makedirs(hooks_dir)