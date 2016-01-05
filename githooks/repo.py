import git
import sys
import os

_repo = None


def get():
    """
    Gets the repo object for the current git repo. This will track back through parent parent directories find the
    repo root.

    :return: The git repo object (object details can be found here http://gitpython.readthedocs.org/en/stable/tutorial.html#meet-the-repo-type)
    """
    global _repo
    if not _repo:
        _repo = git.Repo(os.path.dirname(sys.argv[0]), search_parent_directories=True)
    return _repo


def repo_root():
    """
    Gets the root directory of the git repo

    :return: The root directory of the git repo
    """
    return os.path.dirname(get().git_dir)


def untracked_files():
    """
    Gets a list of the untracked files in the current git repo

    :return: A list of absolute paths to untracked files in the repo.
    """
    repo_root_dir = repo_root()
    return [os.path.join(repo_root_dir, p) for p in get().untracked_files]


def modified_files():
    """
    Gets a list of modified files in the repo.

    :return: A list of absolute paths to all changed files in the repo
    """
    repo_root_dir = repo_root()
    return [os.path.join(repo_root_dir, d.a_path) for d in get().head.commit.diff() if not (d.new_file or d.deleted_file)]


def added_files():
    """
    Gets a list of added files in the repo.

    :return: A list of absolute paths to all added files in the repo
    """
    repo_root_dir = repo_root()
    return [os.path.join(repo_root_dir, d.a_path) for d in get().head.commit.diff() if d.new_file]


def deleted_files():
    """
    Gets a list of deleted files in the repo.

    :return: A list of absolute paths to all deleted files in the repo
    """
    repo_root_dir = repo_root()
    return [os.path.join(repo_root_dir, d.b_path) for d in get().head.commit.diff() if d.deleted_file]


def hook_type_directory(hook_type):
    """
    Gets the directory to install hooks of the specified type to

    :param hook_type: the type of hook to get the install directory for
    :return: The path to install hooks to
    """
    return os.path.join(repo_root(), '.git', 'hooks', hook_type + '.d')


