import subprocess

from . import finders, repo


class HookRunner(object):
    finder_class = None

    def get_process_args(self, *args):
        return args

    def get_process_kwargs(self, **kwargs):
        return kwargs

    def get_finder_class(self):
        return self.finder_class

    def get_finder(self):
        return self.get_finder_class()()

    def run(self):
        args = list(self.get_process_args())

        for k_v in sorted(self.get_process_kwargs().items()):
            args.extend(k_v)

        return sum(subprocess.call([path] + args) for path in self.get_finder())


class PreCommitHookRunner(HookRunner):
    finder_class = finders.PreCommitHookFinder

    def get_process_kwargs(self, **kwargs):
        kwargs.setdefault('--added-files', repo.added_files())
        kwargs.setdefault('--modified-files', repo.modified_files())
        kwargs.setdefault('--deleted-files', repo.deleted_files())
        return super(PreCommitHookRunner, self).get_process_kwargs(**kwargs)
