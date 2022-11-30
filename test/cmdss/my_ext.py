from os.path import join, realpath, dirname
import sys
sys.path.insert(0, join(dirname(realpath(__file__)), '../../'))
from cjutils.cmd import argparse_base


class cmd(argparse_base):
    def __init__(self, opt_argv=..., enable_plugin=False, plugin_dir='cmds') -> None:
        super().__init__(opt_argv=[
            ('a', 'aaa', 'aaaaa', 0, False),
            ('', 'bbb', 'bbbbb', [], False),
            ('c', 'cc', 'ccccccc', '', False),
            ('d', '', 'ddd', False, False),
            ('e', '--ee', 'eeeeeeeeee', True, False)
        ], enable_plugin=False, plugin_dir='cmds')

    def test(self, key, value):
        assert self.get_opt(
            key) == value, f"{self.get_opt(key)} != {value}"
        return 0

    def main(self):
        self.test('aaa', 'valuea')
        self.test('bbb', ['1', '2', '3', '4', '5'])
        self.test('cc', '')
        self.test('d', True)
        self.test('e', False)
        tmp = sys.argv

        sys.argv = "test -a valuea".split()
        self.args = self.parse_args()
        self.test('aaa', 'valuea')
        assert self.hasopt('a')
        assert self.hasopt('aaa')

        sys.argv = "test --aaa valuea".split()
        self.args = self.parse_args()
        self.test('aaa', 'valuea')
        assert self.hasopt('a')
        assert self.hasopt('aaa')

        sys.argv = "test --aaa valuea --bbb 1 2 3 4 5".split()
        self.args = self.parse_args()
        self.test('aaa', 'valuea')
        self.test('bbb', ['1', '2', '3', '4', '5'])
        assert self.hasopt('a')
        assert self.hasopt('bbb')
        assert self.hasopt('c')
        assert self.hasopt('d')
        assert self.hasopt('ee')

        sys.argv = "test --aaa valuea --bbb 1 2 3 4 5".split()
        self.args = self.parse_args()
        self.test('cc', '')

        sys.argv = "test --aaa valuea --bbb 1 2 3 4 5".split()
        self.args = self.parse_args()
        self.test('cc', '')
        self.test('d', False)
        self.test('ee', True)

        sys.argv = "test --aaa valuea --bbb 1 2 3 4 5 -ed".split()
        self.args = self.parse_args()
        self.test('a', 'valuea')
        self.test('bbb', ['1', '2', '3', '4', '5'])
        self.test('aaa', 'valuea')
        self.test('d', True)
        self.test('e', False)
        assert self.hasopt('a')
        assert not self.hasopt('b')
        assert self.hasopt('cc')
        assert self.hasopt('d')
        assert self.hasopt('e')

        sys.argv = tmp
        return 0


if __name__ == '__main__':
    cmd().main()
