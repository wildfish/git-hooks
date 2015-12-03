#!/usr/bin/env python
import sys

import subprocess

from githooks import hooks, repo


def main():
    added_files = repo.added_files()
    modified_files = repo.modified_files()
    deleted_files = repo.deleted_files()

    result = 0

    for path in hooks.PreCommitHookFinder():
        result += subprocess.call(
            [path] +
            ['--added-files'] + added_files +
            ['--modified-files'] + modified_files +
            ['--deleted-files'] + deleted_files
        )

    return result


if __name__ == '__main__':
    sys.exit(main())
