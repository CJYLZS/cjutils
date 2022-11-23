import os
import sys
import time
import pstats
from cProfile import Profile


def analyze(sortby=None, filename=None, stream=None):
    # sortby: ncalls tottime percall cumtime
    def decorator(func):
        def wrapper(*args, **kwargs):
            profile = Profile()
            profile.enable()
            ret = func(*args, **kwargs)
            profile.disable()
            if sortby is not None:
                ps = pstats.Stats(profile, stream=stream).sort_stats(sortby)
            if filename is not None:
                ps.dump_stats(filename)
            else:
                ps.print_stats()
            return ret
        return wrapper
    return decorator


def timer(log_func=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            s = time.time()
            ret = func(*args, **kwargs)
            if callable(log_func):
                log_func(f'{func} cost {round((time.time() - s)*1000, 3)} ms')
            else:
                print(f'{func} cost {round((time.time() - s)*1000, 3)} ms')
            return ret
        return wrapper
    return decorator


@analyze(sortby='ncalls')
@timer(log_func=print)
def test():
    time.sleep(5)
    return 1


if __name__ == '__main__':
    assert test() == 1
