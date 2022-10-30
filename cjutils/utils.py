from datetime import datetime
import os
import sys
import os
import sys
import time
import json
import traceback
import subprocess as sp
import logging

sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)))
from _utils import *
from logger import *

logging._levelToName[logging.WARNING] = 'WARN'
logging._levelToName[logging.CRITICAL] = 'FATAL'


if 'dirs' not in __builtins__.keys():
    __builtins__['dirs'] = []


def now(format='%y%m%d-%H:%M:%S'):
    return datetime.strftime(datetime.now(), format)


def python():
    if is_windows():
        return 'python'
    s, o = sp.getstatusoutput('which python3')
    assert s == 0, f'{o}'
    return o


def me():
    if 'USER' in os.environ:
        return os.environ['USER']
    return run('whoami', show=False)


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


def pexist(d):
    return pexists(d)


def clone(url, depth=1, dst_dir='.', reclone=False):
    dst_dir = expanduser(dst_dir)
    if dst_dir != '.' and pexist(dst_dir):
        if not reclone:
            return
        run(f'rm -rf {dst_dir}')

    def _clone():
        runok(f'git clone {url} --depth={depth} {dst_dir}')
    retry(_clone)


def lns(source, dest, safe=True):
    # dest -> source
    assert pexist(source), f'{source} not exist'
    dest = expanduser(dest)
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
    source = expanduser(source)
    if not pexist(source):
        warn(f'backup: {source} not exist')
        return
    backup_files = []
    full = True
    for i in range(1, max_count + 1):
        new_name = source + f'.{i}'
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


def pushd(dir=None):
    if not dir:
        __builtins__['dirs'].append(curdir())
    else:
        assert pexist(dir), f'{dir} not exist'
        __builtins__['dirs'].append(os.path.realpath(dir))


def cd(path, show=True):
    path = expanduser(path)
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
