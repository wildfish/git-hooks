import os


def get_hook_script_dir():
    return os.path.join(os.path.dirname(__file__), 'hook_scripts')


def get_hook_names():
    return os.listdir(get_hook_script_dir())
