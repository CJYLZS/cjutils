import os
import sys
import subprocess as sp

from uuid import uuid4


def red(str):
    return f'\033[31m{str}\033[0m'


def green(str):
    return f'\033[32m{str}\033[0m'


def yellow(str):
    return f'\033[33m{str}\033[0m'


def blue(str):
    return f'\033[34m{str}\033[0m'


def purple(str):
    return f'\033[35m{str}\033[0m'


def cyan(str):
    return f'\033[36m{str}\033[0m'


def lred(str):
    return f'\033[1;31m{str}\033[0m'


def lgreen(str):
    return f'\033[1;32m{str}\033[0m'


def lyellow(str):
    return f'\033[1;33m{str}\033[0m'


def lblue(str):
    return f'\033[1;34m{str}\033[0m'


def lpurple(str):
    return f'\033[1;35m{str}\033[0m'


def lcyan(str):
    return f'\033[1;36m{str}\033[0m'

# dir


def pexists(path):
    return os.path.exists(path)


def pjoin(*args):
    return os.path.join(*args)


def home():
    return os.environ["HOME"]


def expanduser(path):
    return os.path.expanduser(path)


def curdir():
    return os.path.realpath(os.curdir)


def dirname(path):
    return os.path.dirname(path)


# platform


def is_linux():
    return sys.platform == 'linux'


def is_windows():
    return sys.platform == 'win32'


def is_docker():
    return pexists('/.dockerenv')

# tools


def get_env(key):
    return os.environ.get(key, None)


# file


def rm(filename):
    os.remove(filename)


def cp(source, dest, args=''):
    s, r = sp.getstatusoutput(f'cp {args} {source} {dest}')
    assert s == 0, r
    return s


def mv(source, dest, args=''):
    s, r = sp.getstatusoutput(f'mv {args} {source} {dest}')
    assert s == 0, r
    return s


def create_empty_file(filename):
    if '/' in filename:
        dirname = os.path.dirname(os.path.realpath(dirname))
        if not os.path.exists(dirname):
            os.makedirs(dirname)
    with open(filename, 'w'):
        pass


def get_tmp_file():
    assert sys.platform == 'linux', 'only linux'
    filename = f'/tmp/tmp_{str(uuid4())}'
    create_empty_file(filename)
    return filename


class FileLock:
    def __init__(self, lockFile=None) -> None:
        if not lockFile:
            self.lockFile = get_tmp_file()
        else:
            self.lockFile = lockFile
            create_empty_file(self.lockFile)
        self.__f = None
        self.__fcntl = __import__('fcntl')

    def __del__(self):
        os.remove(self.lockFile)

    def lock(self):
        assert self.__f is None, 'dead lock'
        self.__f = open(self.lockFile, 'r+')
        self.__fcntl.flock(self.__f.fileno(), self.__fcntl.LOCK_EX)

    def unlock(self):
        if not self.__f:
            return
        self.__fcntl.flock(self.__f.fileno(), self.__fcntl.LOCK_UN)
        self.__f.close()
        self.__f = None

    def __enter__(self):
        self.lock()

    def __exit__(self, *args):
        self.unlock()
