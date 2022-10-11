from uuid import uuid4
from datetime import datetime
import os
import sys
import re
import os
import sys
import time
import json
import base64
import traceback
import subprocess as sp
import logging
logging._levelToName[logging.WARNING] = 'WARN'
logging._levelToName[logging.CRITICAL] = 'FATAL'


if 'dirs' not in __builtins__.keys():
    __builtins__['dirs'] = []


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


class ColorFormatter(logging.Formatter):
    def __init__(self, fmt: str = None, datefmt: str = '%y%m%d|%H:%M:%S', style='{', validate: bool = True) -> None:
        self.fmt = fmt
        self.datefmt = datefmt
        self.style = style
        self.validate = validate
        self.formats = {
            logging.DEBUG: f"{lgreen('{levelname: <6}')}{green('{asctime: <16}')}{{message}}",
            logging.INFO: f"{lgreen('{levelname: <6}')}{green('{asctime: <16}')}{{message}}",
            logging.WARNING: f"{lyellow('{levelname: <6}')}{yellow('{asctime: <16}')}{{message}}",
            logging.ERROR: f"{lred('{levelname: <6}')}{red('{asctime: <16}')}{{message}}",
            logging.CRITICAL: f"{lred('{levelname: <6}')}{red('{asctime: <16}')}{{message}}",
        }

    def format(self, record):
        if not self.fmt:
            log_fmt = self.formats[record.levelno]
        else:
            log_fmt = self.fmt
        formatter = logging.Formatter(
            log_fmt, style=self.style, datefmt=self.datefmt)
        return formatter.format(record)


class NoColorFormatter(logging.Formatter):
    """
    Log formatter that strips terminal colour
    escape codes from the log message.
    """

    def __init__(self, fmt: str = None, datefmt: str = None, style='{', validate: bool = True) -> None:
        self.fmt = fmt
        self.datefmt = datefmt
        self.style = style
        self.validate = validate

    # Regex for ANSI colour codes
    ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

    def format(self, record):
        """Return logger message with terminal escapes removed."""
        record.msg = re.sub(self.ANSI_RE, "", record.msg)
        return logging.Formatter(fmt=self.fmt, datefmt=self.datefmt, style=self.style, validate=self.validate).format(record)


logging.basicConfig(
    level=logging.DEBUG,
    handlers=[]
)
_basic_logger = logging.getLogger('yutils_ylog_logger')
_basic_log_handler = logging.StreamHandler()
_basic_log_handler.setFormatter(ColorFormatter())
_basic_logger.addHandler(_basic_log_handler)


def create_empty_file(filename):
    if '/' in filename:
        dirname = os.path.dirname(os.path.realpath(dirname))
        if not os.path.exists(dirname):
            os.makedirs(dirname)
    with open(filename, 'w'):
        pass


def rm(filename):
    os.remove(filename)


def get_tmp_file():
    assert sys.platform == 'linux', 'only linux'
    filename = f'/tmp/tmp_{str(uuid4())}'
    create_empty_file(filename)
    return filename


def is_linux():
    return sys.platform == 'linux'


if is_linux():
    import fcntl


class fileLock:
    def __init__(self, lockFile=None) -> None:
        if not lockFile:
            self.lockFile = get_tmp_file()
        else:
            self.lockFile = lockFile
            create_empty_file(self.lockFile)
        self.__f = None

    def __del__(self):
        rm(self.lockFile)

    def lock(self):
        assert self.__f is None, 'dead lock'
        self.__f = open(self.lockFile, 'r+')
        fcntl.flock(self.__f.fileno(), fcntl.LOCK_EX)

    def unlock(self):
        if not self.__f:
            return
        fcntl.flock(self.__f.fileno(), fcntl.LOCK_UN)
        self.__f.close()
        self.__f = None

    def __enter__(self):
        self.lock()

    def __exit__(self, *args):
        self.unlock()


class ylog:
    def __init__(self, lockFile=None, enableLineno=True, logger=_basic_logger) -> None:
        if lockFile and sys.platform == 'linux':
            self.lock = fileLock(lockFile=lockFile)
        else:
            self.lock = None
        self.__logger = logger
        self.__enable_lineno = enableLineno

    def enable_lineno(self):
        self.__enable_lineno = True

    def disable_lineno(self):
        self.__enable_lineno = False

    def __get_frame_str(self, color=lgreen):
        if not self.__enable_lineno:
            return ''
        frame = sys._getframe(2)
        if frame.f_code.co_filename == os.path.realpath(__file__):
            frame = frame.f_back
        return f' {color("<<")} {os.path.realpath(frame.f_code.co_filename)}-{frame.f_lineno}'

    def debug(self, *args):
        if self.lock is not None:
            with self.lock:
                self.__logger.debug(
                    " ".join([f'{arg}' for arg in args]) + self.__get_frame_str())
        else:
            self.__logger.debug(
                " ".join([f'{arg}' for arg in args]) + self.__get_frame_str())

    def info(self, *args):
        if self.lock is not None:
            with self.lock:
                self.__logger.info(" ".join([f'{arg}' for arg in args]))
        else:
            self.__logger.info(" ".join([f'{arg}' for arg in args]))

    def warn(self, *args):
        if self.lock is not None:
            with self.lock:
                self.__logger.warning(
                    " ".join([f'{arg}' for arg in args]) + self.__get_frame_str(color=lyellow))
        else:
            self.__logger.warning(
                " ".join([f'{arg}' for arg in args]) + self.__get_frame_str(color=lyellow))

    def err(self, *args):
        if self.lock is not None:
            with self.lock:
                self.__logger.error(
                    " ".join([f'{arg}' for arg in args]) + self.__get_frame_str(color=lred))
        else:
            self.__logger.error(
                " ".join([f'{arg}' for arg in args]) + self.__get_frame_str(color=lred))

    def fatal(self, *args):
        if self.lock is not None:
            with self.lock:
                self.__logger.critical(
                    " ".join([f'{arg}' for arg in args]) + self.__get_frame_str(color=lred))
        else:
            self.__logger.critical(
                " ".join([f'{arg}' for arg in args]) + self.__get_frame_str(color=lred))


if "logger" not in __builtins__.keys():
    __builtins__["logger"] = ylog()


def get_logger(
        name=None,
        level=logging.WARNING,
        filename=None,
        fmt=None,
        style="{",
        datefmt='%y%m%d|%H:%M:%S',
        useFileLock=False,
        enableLineno=True,
        add_new_handler=False):
    if not name:
        name = sys._getframe().f_back.f_code.co_filename
    logger = logging.getLogger(name=name)
    if len(logger.handlers) > 0 and not add_new_handler:
        return logger
    logger.setLevel(level=level)
    if filename:
        if not fmt:
            fmt = '{name} {levelname: <6}{asctime: <8}: {message}'
        handler = logging.FileHandler(filename=filename)
        formatter = NoColorFormatter(
            fmt=fmt, datefmt=datefmt, style=style)
    else:
        handler = logging.StreamHandler()
        formatter = ColorFormatter(
            fmt=fmt, datefmt=datefmt, style=style)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    if not useFileLock:
        return ylog(enableLineno=enableLineno, logger=logger)
    if filename:
        return ylog(lockFile=filename + '.lck', enableLineno=enableLineno, logger=logger)
    assert 'CJUTILS_LOCK_FILE' in os.environ.keys(
    ), 'get logger failed use file or set lock file in env: CJUTILS_LOCK_FILE'
    return ylog(lockFile=os.environ["CJUTILS_LOCK_FILE"], enableLineno=enableLineno, logger=logger)


def debug(*args):
    __builtins__["logger"].debug(*args)


def info(*args):
    __builtins__["logger"].info(*args)


def warn(*args):
    __builtins__["logger"].warn(*args)


def err(*args):
    __builtins__["logger"].err(*args)


def fatal(*args):
    __builtins__["logger"].fatal(*args)


def now(format='%y%m%d-%H:%M:%S'):
    return datetime.strftime(datetime.now(), format)


def is_windows():
    return sys.platform == 'win32'


def is_docker():
    return pexist('/.dockerenv')


def python():
    if is_windows():
        return 'python'
    return runok('which python3')


def replace_home(path):
    return os.path.expanduser(path)


def __run(cmd):
    if is_windows():
        cmd = cmd.replace('sudo', '').strip()
    return sp.getstatusoutput(cmd)


def sys_run(cmd, show=True) -> int:
    if show:
        info(f'{lgreen("-")} {cmd}')
    return os.system(cmd)


def run(cmd, show=True) -> str:
    if show:
        info(f'{lgreen("-")} {cmd}')
    code, output = __run(cmd)
    if code != 0:
        warn(code, output)
    return output


def runex(cmd, show=True) -> tuple:
    if show:
        info(f'{lyellow("-")} {cmd}')
    code, output = __run(cmd)
    if code != 0:
        warn(code, output)
    return code, output


def runok(cmd, show=True) -> tuple:
    if show:
        info(f'{lred("-")} {cmd}')
    code, output = __run(cmd)
    if code != 0:
        err(code, output)
        assert code == 0, f'{cmd} failed'
    return output


def pexist(path):
    return os.path.exists(path)


def pjoin(*args):
    return os.path.join(*args)


def home():
    return os.environ["HOME"]


def me():
    if 'USER' in os.environ:
        return os.environ['USER']
    return run('whoami', show=False)


def check_file(file_name):
    code, _ = runex(f'which {file_name}')
    return code == 0


def check_pkg(file_name, package_name):
    code, output = runex(f'which {file_name}')
    if code != 0:
        warn(f'not found {file_name}, try to install {package_name}')
        code, output = runex(f'sudo apt install -y {package_name}')
        if code != 0:
            warn(output)
            err(f'auto install {package_name} failed')
            exit(-1)
        code, output = runex(f'which {file_name}')
        if code != 0:
            warn(output)
            err(f'auto install {package_name} failed')
            exit(-1)


def get_pip():
    if is_windows():
        return 'python -m pip'
    return f'{python()} -m pip'


def import_module(mod, mod_name=None):
    if mod_name is None:
        mod_name = mod

    def _import_module():
        try:
            __import__(mod)
        except ModuleNotFoundError:
            warn(f'{mod} not found try to install {mod_name}')
            runok(f'{get_pip()} install {mod_name}')
        return __import__(mod)
    return retry(_import_module, interval=1)


def clone(url, depth=1, dst_dir='.'):
    dst_dir = replace_home(dst_dir)
    if dst_dir != '.' and pexist(dst_dir):
        run(f'rm -rf {dst_dir}')

    def _clone():
        runok(f'git clone {url} --depth={depth} {dst_dir}')
    retry(_clone)


def cp(source, dest, args=''):
    runok(f'cp {args} {source} {dest}')


def mv(source, dest, args=''):
    runok(f'mv {args} {source} {dest}')


def lns(source, dest, safe=True):
    # dest -> source
    assert pexist(source), f'{source} not exist'
    dest = replace_home(dest)
    if pexist(dest):
        if safe:
            backup(dest)
        else:
            rm(dest)
    source = os.path.realpath(source)
    runok(f'ln -s {source} {dest}')


def sort_by_mtime(files: list):
    return sorted(files, key=lambda f: os.stat(f).st_ctime)


def backup(source, max_count=5):
    source = replace_home(source)
    if not pexist(source):
        err(f'{source} not exist')
        return
    basename = os.path.basename(source)
    dname = os.path.dirname(source)
    if '.' in basename:
        *backup_basename, _type = basename.split('.')
        backup_basename = '.'.join(backup_basename)
    else:
        backup_basename = basename
        _type = None
    backup_name = os.path.join(dname, backup_basename)
    backup_files = []
    full = True
    for i in range(1, max_count + 1):
        if _type is None:
            new_name = backup_name + f'_{i}'
        else:
            new_name = backup_name + f'_{i}.{_type}'
        if not pexist(new_name):
            backup_name = new_name
            full = False
            break
        backup_files.append(new_name)
    if full:
        backup_files = sort_by_mtime(backup_files)
        rm(backup_files[0])
        backup_name = backup_files[0]

    if is_windows():
        cmd = 'move'
    else:
        cmd = 'mv'
    runok(f'{cmd} {source} {backup_name}')


def curdir():
    return os.path.realpath(os.curdir)


def dirname(path):
    return os.path.dirname(path)


def pushd(dir=None):
    if not dir:
        __builtins__['dirs'].append(curdir())
    else:
        assert pexist(dir), f'{dir} not exist'
        __builtins__['dirs'].append(os.path.realpath(dir))


def cd(path, show=True):
    path = replace_home(path)
    assert pexist(path), f'{path} not exist'
    if os.path.isfile(path):
        os.chdir(dirname(path))
    else:
        os.chdir(path)
    if show:
        info(f'cd {path}')


def popd():
    assert len(__builtins__['dirs']
               ) > 0, 'not dir in __builtins__.dirs'
    d = __builtins__['dirs'].pop()
    cd(d)
    return d


def repo_root_dir(path):
    assert pexist(path), f"{path} not exist"
    real_path = os.path.realpath(path)
    while real_path != '/':
        if pexist(pjoin(real_path, '.git')):
            return real_path
        real_path = dirname(real_path)
    assert False, f'{path} not in git repo'


def list_all_file(dir):
    for tmp in os.listdir(dir):
        if not os.path.isdir(os.path.join(dir, tmp)):
            yield os.path.join(dir, tmp)
        else:
            yield from list_all_file(os.path.join(dir, tmp))


def retry(func, times=5, interval=3):
    res = None
    for t in range(1, times + 1):
        try:
            res = func()
        except Exception as e:
            traceback.print_exc()
            warn(f'run {func} failed {t} time(s)\n{e}')
            info(f'wait {interval} second(s)')
            time.sleep(interval)
            continue
        break
    return res


def dump_json(d: dict):
    return '\n' + json.dumps(d, indent=4, separators=',:', ensure_ascii=True)


def get_env(key):
    return os.environ.get(key, None)


def set_env(key, val="1", overwrite=True):
    if not overwrite:
        assert key not in os.environ, f"{key} exist in environment val is {os.environ[key]} should overwrite?"
    os.environ[key] = str(val)
    return os.environ[key]


####################################################---use site-packages utils---####################################################


def get_clipboard():
    pyperclip = import_module('pyperclip')
    return pyperclip.paste()


def set_clipboard(_str):
    pyperclip = import_module('pyperclip')
    pyperclip.copy(_str)


def container_running(container_name):
    docker = import_module('docker')
    client = docker.from_env()
    return container_name in [c.name for c in client.containers.list(all=False)]
