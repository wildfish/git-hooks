try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser

try:
    from urllib.parse import urlsplit
except ImportError:
    from urlparse import urlsplit

try:
    FileExistsException = FileExistsError
except NameError:
    FileExistsException = FileExists  # noqa

__all__ = [ConfigParser, urlsplit, FileExistsError]
