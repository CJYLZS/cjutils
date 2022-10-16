import re
import os
import sys
import logging
sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)))
from _utils import *


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
_basic_logger.handlers = []
_basic_logger.addHandler(_basic_log_handler)


class ylog:
    def __init__(self, lockFile=None, enableLineno=True, logger=_basic_logger, showFileLevel=3) -> None:
        if lockFile and sys.platform == 'linux':
            self.lock = FileLock(lockFile=lockFile)
        else:
            self.lock = None
        self.__logger = logger
        self.__enable_lineno = enableLineno
        self.__show_file_level = showFileLevel

    def enable_lineno(self):
        self.__enable_lineno = True

    def disable_lineno(self):
        self.__enable_lineno = False

    def get_last_name(self, filename, count):
        res = []
        for _ in range(count):
            filename = os.path.split(filename)
            if filename[1] == '':
                res.insert(0, filename[0])
                break
            res.insert(0, filename[1])
            filename = filename[0]
        return os.path.join(*res)

    def __get_frame_str(self, color=lgreen):
        if not self.__enable_lineno:
            return ''
        frame = sys._getframe(2)
        if is_windows():
            if frame.f_code.co_filename.lower() == os.path.realpath(__file__).lower():
                frame = frame.f_back
        elif frame.f_code.co_filename == os.path.realpath(__file__):
            frame = frame.f_back
        filename = self.get_last_name(os.path.realpath(
            frame.f_code.co_filename), self.__show_file_level)
        return f' {color("<<")} {filename}:{frame.f_lineno}'

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
        resetHandler=False,
        overwriteDefaultLogger=True,
        alwaysUseStdOut=True,
        showFileLevel=3):
    if not name:
        name = sys._getframe(1).f_code.co_filename
    logger = logging.getLogger(name=name)
    logger.setLevel(level=level)

    def add_handler(formatter: logging.Formatter, handler: logging.Handler):
        if resetHandler:
            logger.handlers = []
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    if filename:
        _dir = os.path.dirname(filename)
        if _dir and not pexists(_dir):
            os.makedirs(_dir)
        if not fmt:
            _fmt = '{levelname: <6}{asctime: <8}: {message} {name}'
        handler = logging.FileHandler(filename=filename, encoding='utf-8')
        formatter = NoColorFormatter(
            fmt=_fmt, datefmt=datefmt, style=style)
        add_handler(formatter, handler)

    if not filename or alwaysUseStdOut:
        handler = logging.StreamHandler()
        formatter = ColorFormatter(
            fmt=fmt, datefmt=datefmt, style=style)
        add_handler(formatter, handler)

    def return_ylog(ylog: ylog):
        if overwriteDefaultLogger:
            __builtins__["logger"] = ylog
        return ylog
    if not useFileLock:
        return return_ylog(ylog(enableLineno=enableLineno, logger=logger, showFileLevel=showFileLevel))
    if filename:
        return return_ylog(ylog(lockFile=filename + '.lck', enableLineno=enableLineno, logger=logger, showFileLevel=showFileLevel))
    assert 'CJUTILS_LOCK_FILE' in os.environ.keys(
    ), 'get logger failed use file or set lock file in env: CJUTILS_LOCK_FILE'
    return return_ylog(ylog(lockFile=os.environ["CJUTILS_LOCK_FILE"], enableLineno=enableLineno, logger=logger, showFileLevel=showFileLevel))


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
