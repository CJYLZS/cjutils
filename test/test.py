from os.path import join, realpath, dirname
import sys
sys.path.insert(0, join(dirname(realpath(__file__)), '../cjutils/'))


def test_argparse_base():
    tmp = sys.argv
    from cmd import argparse_base

    class fuck(argparse_base):
        def __init__(self, opt_argv=[
            ('a', 'aaa', 'aaaaa', 0, False),
            ('', 'bbb', 'bbbbb', [], False),
            ('c', 'cc', 'ccccccc', '', False),
            ('d', '', 'ddd', False, False),
            ('e', '--ee', 'eeeeeeeeee', True, False),
        ], enable_plugin=True, plugin_dir='cmdss') -> None:
            super().__init__(opt_argv, enable_plugin, plugin_dir)

        def test(self, key, value):
            assert self.get_opt(
                key) == value, f"{self.get_opt(key)} != {value}"
            return 0

    sys.argv = "test -a valuea".split()
    fuck().test('aaa', 'valuea')
    sys.argv = "test --aaa valuea".split()
    fuck().test('aaa', 'valuea')
    sys.argv = "test --aaa valuea --bbb 1 2 3 4 5".split()
    fuck().test('aaa', 'valuea')
    fuck().test('bbb', ['1', '2', '3', '4', '5'])
    sys.argv = "test --aaa valuea --bbb 1 2 3 4 5".split()
    fuck().test('cc', '')
    sys.argv = "test --aaa valuea --bbb 1 2 3 4 5".split()
    fuck().test('cc', '')
    fuck().test('d', False)
    fuck().test('ee', True)
    sys.argv = "test --aaa valuea --bbb 1 2 3 4 5 -ed".split()
    fuck().test('a', 'valuea')
    fuck().test('bbb', ['1', '2', '3', '4', '5'])
    fuck().test('aaa', 'valuea')
    fuck().test('d', True)
    fuck().test('e', False)

    sys.argv = "test my -a valuea --bbb 1 2 3 4 5 -de".split()
    fuck()

    sys.argv = tmp


if __name__ == '__main__':
    test_argparse_base()
