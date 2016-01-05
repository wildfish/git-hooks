import argparse


def pre_commit():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='*')
    parser.add_argument('--modified-files', nargs='*', dest='modified')
    parser.add_argument('--added-files', nargs='*', dest='added')
    parser.add_argument('--deleted-files', nargs='*', dest='deleted')

    return parser.parse_args()
