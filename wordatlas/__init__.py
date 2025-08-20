from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

try:
    __version__ = _version("wordatlas")
except PackageNotFoundError:
    __version__ = "0.1.0"
