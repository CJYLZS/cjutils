import os
import sys
import time
import traceback
sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)))
from logger import *

logging._levelToName[logging.WARNING] = 'WARN'
logging._levelToName[logging.CRITICAL] = 'FATAL'


def retry(func, times=5, interval=3):
    exception = None
    try:
        res = func()
    except Exception as e:
        exception = e
        for t in range(1, times):
            if exception is None:
                break
            info(traceback.format_exc())
            warn(f'run {func} failed {t} time(s)\n{exception}')
            info(f'wait {interval} second(s)')
            time.sleep(interval)
            try:
                res = func()
                exception = None
            except Exception as e:
                exception = e
        if not exception is None:
            # finally failed
            err(f'{func} already failed {times} time(s) retry finally failed!!!')
            assert False
        else:
            warn(f'{func} finally succeed after {times} time(s) retry ')
    return res


def Dretry(times=5, interval=3):
    def decorator(func):
        def wrapper(*args, **kwargs):
            exception = None
            try:
                res = func()
            except Exception as e:
                exception = e
                for t in range(1, times):
                    if exception is None:
                        break
                    info(traceback.format_exc())
                    warn(f'run {func} failed {t} time(s)\n{exception}')
                    info(f'wait {interval} second(s)')
                    time.sleep(interval)
                    try:
                        res = func(*args, **kwargs)
                        exception = None
                    except Exception as e:
                        exception = e
                if not exception is None:
                    # finally failed
                    err(f'{func} already failed {times} time(s) retry finally failed!!!')
                    assert False
                else:
                    warn(f'{func} finally succeed after {times} time(s) retry ')
            return res
        return wrapper
    return decorator


def test():
    logger = get_logger(name='test', level=logging.INFO,
                        overwriteDefaultLogger=False)

    def test1():
        # failed 4 times
        i = 0

        def failed_func():
            nonlocal i
            while i < 4:
                i += 1
                assert False, 'failed'
            return 1
        assert retry(failed_func, interval=0) == 1

    def test2():
        # failed 4 times
        i = 0

        @Dretry(5, 0)
        def failed_func():
            nonlocal i
            while i < 4:
                i += 1
                assert False, 'failed'
            return 1
        assert failed_func() == 1

    test1()
    test2()
    logger.info('pass')


if __name__ == '__main__':
    get_logger(overwriteDefaultLogger=True, level=logging.ERROR)
    test()
