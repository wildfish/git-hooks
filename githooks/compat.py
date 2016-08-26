try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser

try:
    from urllib.parse import urlsplit, urljoin, urlencode
except ImportError:
    from urlparse import urlsplit, urljoin, urlencode

try:
    FileExistsException = FileExistsError
except NameError:
    FileExistsException = OSError

__all__ = [ConfigParser, urlsplit, urljoin, urlencode, FileExistsException]
