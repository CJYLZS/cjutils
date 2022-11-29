import os
import sys
sys.path.append(os.path.realpath(os.path.dirname(__file__)))
from utils import *


class cmd_base():
    __cmd_plugin_example = \
        '''
from cjutils.cmd import *


class cmd(cmd_base):
    def __init__(self, options_argv=..., brief_intro="", enable_plugins=True) -> None:
        super().__init__([
            ('a', 'along', 'args a', False, False),
            ('b', 'blong', 'args b', -1, False),
            ('c', 'clong', 'args c', "", False),
        ], brief_intro="an example plugin", enable_plugins=False)

    def main(self):

        return 0
'''

    def __get_arg_short(self, arg):
        return arg[0]

    def __get_arg_long(self, arg):
        return arg[1]

    def __get_arg_help(self, arg):
        return arg[2]

    def __get_arg_default_value(self, arg):
        return arg[3]

    def __get_arg_required(self, arg):
        return arg[4]

    def __is_long_name(self, name):
        return len(name) > 1

    def __is_short_name(self, name):
        return len(name) == 1

    def __write_example_plugin(self):
        if not pexist(self.plugins_dir):
            os.makedirs(self.plugins_dir)

        with open(pjoin(self.plugins_dir, 'example_ext.py'), 'w') as f:
            f.write(self.__cmd_plugin_example)

        sys.exit(0)

    def __init_vars(self):
        self.sys_args = {}
        self.sys_short_args = {}
        self.sys_targets = []
        self.opt_args = {
            "help": ("h", "help", "print help", False, False),
            "example": ("", "example", "create a example plugin into ./cmds/", False, False),
        }
        self.opt_short_args = {}

    def __init_dirs(self, plugin_dir):
        if plugin_dir is not None and pexist(plugin_dir):
            self.plugins_dir = plugin_dir
        else:
            self.plugins_dir = None
        self.exec_dir = os.path.realpath(".")
        self.file_dir = os.path.realpath(dirname(sys.argv[0]))
        self.cmd_dir = os.path.realpath(dirname(__file__))
        if self.plugins_dir is None:
            self.plugins_dir = pjoin(self.exec_dir, 'cmds')
        if pexist(self.plugins_dir):
            sys.path.append(self.plugins_dir)

    def __init_opt_args(self, options_argv):
        for _, arg in self.opt_args.items():
            self.opt_short_args[self.__get_arg_short(arg)] = arg

        for arg in options_argv:
            assert len(
                arg) == 5, "argv: ([short opt],  [long opt], [help info], [default value], [required])"
            long_name = self.__get_arg_long(arg)
            assert len(long_name) > 1, f'long name length must more than 1'
            assert long_name not in self.opt_args.keys(), f"{arg} duplicate"
            self.opt_args[long_name] = arg
            short_name = self.__get_arg_short(arg)
            if len(short_name) > 0:
                self.opt_short_args[short_name] = arg

    def __is_opt(self, _str):
        rule1 = re.compile(r'-[a-zA-Z]+')
        rule2 = re.compile(r'--[a-zA-Z]+')
        return len(re.sub(rule1, "", _str)) == 0 or len(re.sub(rule2, "", _str)) == 0

    def __init_sys_argv(self):

        def add_to_sys_arg(arg, value):
            self.sys_args[self.__get_arg_long(arg)] = value
            self.sys_short_args[self.__get_arg_short(arg)] = value

        def solve_arg(arg, i) -> int:
            # return index
            default_value = self.__get_arg_default_value(arg)
            if isinstance(default_value, bool):
                add_to_sys_arg(arg, True)
            elif isinstance(default_value, str):
                if i + 1 < len(sys.argv) and not self.__is_opt(sys.argv[i + 1]):
                    add_to_sys_arg(arg, sys.argv[i + 1])
                    i += 1
                else:
                    add_to_sys_arg(arg, default_value)
            elif isinstance(default_value, int):
                if i + 1 < len(sys.argv) and not self.__is_opt(sys.argv[i + 1]):
                    add_to_sys_arg(arg, int(sys.argv[i + 1]))
                    i += 1
                else:
                    add_to_sys_arg(arg, default_value)
            else:
                err(f'args value type can\'t be {type(default_value)} type')
                raise TypeError
            return i
        i = 1
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg.startswith('--'):
                opt = arg[2:]
                assert opt in self.opt_args, f'unknown opt: {opt}'
                arg = self.opt_args[opt]
                i = solve_arg(arg, i)
            elif arg.startswith('-'):
                opt = arg[1:]
                for o in opt:
                    assert o in self.opt_short_args, f'unknown opt: {opt}'
                    arg = self.opt_short_args[o]
                    i = solve_arg(arg, i)
            else:
                self.sys_targets.append(arg)
            i += 1

    def __check_required(self):
        for k in self.opt_args.keys():
            arg = self.opt_args[k]
            if self.__get_arg_required(arg):
                short_name = self.__get_arg_short(arg)
                long_name = self.__get_arg_long(arg)
                if short_name not in self.sys_short_args.keys() and long_name not in self.sys_args.keys():
                    err(f'-{short_name} or --{long_name} is required!')
                    assert False, "cmd check required arg failed"

    def __print_help(self):
        help_info = green("\nylzs cmd frame v0.1\n\n")
        help_info += yellow(f"{'usage:': <8}") + \
            '... [plugin] [options] [targets]\n'
        help_info += yellow(f"{'intro:': <8}") + self.brief_intro + '\n\n'
        if self.__enable_plugins and pexist(self.plugins_dir):
            tmp = ''
            flag = '_ext.py'
            count = 0
            for plugin in os.listdir(self.plugins_dir):
                if plugin.endswith(flag):
                    ext_name = plugin[:-len(flag)]
                    if ext_name == 0:
                        continue
                    ext = __import__(plugin[:plugin.rfind('.')])
                    tmp += f'{ext_name: <24}{ext.cmd().get_help()}\n'
                    count += 1
            if count > 0:
                help_info += f'{green("plugins:")}\n\n{tmp}\n'

        args = set()
        for _, val in self.opt_short_args.items():
            args.add(val)
        for _, val in self.opt_args.items():
            args.add(val)
        args = sorted(args)
        help_info += green('options:\n\n')
        for arg in args:
            val_type = type(self.__get_arg_default_value(arg)).__name__
            required = red('required') if self.__get_arg_required(
                arg) else green('optional')
            if len(self.__get_arg_short(arg)) > 0:
                arg_short_help = f'{"-"+self.__get_arg_short(arg): <4}'
            else:
                arg_short_help = f'{"": <4}'
            help_info += f'{arg_short_help}{"--"+self.__get_arg_long(arg): <20}{self.__get_arg_help(arg): <60}{val_type: <10}{required}\n'
        print(help_info)
        sys.exit(0)

    def __skip_into_plugin(self):
        if len(sys.argv) < 2 or sys.argv[1].startswith('-'):
            # no plugin need to load
            return

        plugin_name = sys.argv[1] + '_ext'
        plugin_file_name = pjoin(self.plugins_dir, plugin_name + '.py')
        if not pexist(plugin_file_name):
            err(os.path.realpath(plugin_file_name), 'is not exist')
            sys.exit(-1)
        sys.argv.remove(sys.argv[1])
        ext = __import__(plugin_name)
        sys.exit(ext.cmd().main())

    def __enabled(self, short_name="", long_name=""):
        assert short_name in self.opt_short_args or long_name in self.opt_args, f"in __enabled: {short_name} and {long_name} not exist"
        res = short_name in self.sys_short_args or long_name in self.sys_args
        return res

    def __init__(self, options_argv=[], brief_intro="", enable_plugins=True, plugin_dir=None, enable_empty_options=True) -> None:
        self.brief_intro = brief_intro
        if get_env("CMD_BASE_GET_HELP"):
            return
        self.__enable_plugins = enable_plugins
        self.__init_vars()
        self.__init_dirs(plugin_dir)
        if enable_plugins:
            self.__skip_into_plugin()
        self.__init_opt_args(options_argv)
        self.__init_sys_argv()
        if self.__enabled('h', 'help') or (len(sys.argv) == 1 and not enable_empty_options):
            self.print_help()
        elif self.__enabled('', 'create_example'):
            self.__write_example_plugin()
        self.__check_required()

    def init_ext_file(self, ext_file):
        # if this module is installed over pip, then don't need add extra search path into plugin_ext.py
        content = f'import sys\nsys.path.append(r"{self.cmd_dir}")\n{">>> auto import from cmd_base <<<":#^80}\n'
        with open(ext_file, 'r+') as f:
            d = f.read(1024)
            f.seek(0)
            if content in d:
                return
            d = content + d
            f.write(d)

    def print_help(self):
        set_env("CMD_BASE_GET_HELP")
        self.__print_help()

    def get_opt(self, opt: str):
        if self.__is_short_name(opt):
            if opt not in self.opt_short_args.keys():
                err(f'unknown opt -{opt}')
                assert False, 'cmd_base get_opt failed'
            if opt not in self.sys_short_args.keys():
                return self.__get_arg_default_value(self.opt_short_args[opt])
            return self.sys_short_args[opt]
        elif self.__is_long_name(opt):
            if opt not in self.opt_args.keys():
                err(f'unknown opt --{opt}')
                assert False, 'cmd_base get_opt failed'
            if opt not in self.sys_args.keys():
                return self.__get_arg_default_value(self.opt_args[opt])
            return self.sys_args[opt]
        else:
            err(f'unknown opt {opt}')
            assert False, 'cmd_base get_opt failed'

    def sys_has_opt(self, opt: str):
        if self.__is_short_name(opt):
            if opt not in self.opt_short_args.keys():
                err(f'unknown opt -{opt}')
                assert False, 'cmd_base sys_has_opt failed'
            return opt in self.sys_short_args
        elif self.__is_long_name(opt):
            if opt not in self.opt_args.keys():
                err(f'unknown opt --{opt}')
                assert False, 'cmd_base sys_has_opt failed'
            return opt in self.sys_args
        else:
            err(f'unknown opt {opt}')
            assert False, 'cmd_base sys_has_opt failed'

    def get_targets(self):
        return self.sys_targets

    def get_help(self):
        return self.brief_intro


import argparse


class argparse_base(argparse.ArgumentParser):
    def __skip_into_plugin(self, plugin):
        plugin_py = os.path.join(self.plugin_dir, f'{plugin}_ext.py')
        assert os.path.exists(
            plugin_py), f'{os.path.realpath(plugin_py)} not exist!'
        sys.argv.remove(plugin)
        ext = __import__(plugin_py)
        sys.exit(ext.cmd().main())

    def __print_error(self, info):
        print(info)
        sys.exit(255)

    def __get_help_info(self, args):
        pass

    def __get_names_from_opt_args(self, args):
        short_name, long_name = args['sname'], args['lname']
        assert not (len(short_name) == 0 and len(long_name) ==
                    0), 'both short and long name is empty!'
        if short_name and not short_name.startswith('-'):
            short_name = '-' + short_name
        if long_name and not long_name.startswith('--'):
            long_name = '--' + long_name
        if short_name and long_name:
            return (short_name, long_name)
        elif short_name:
            return (short_name,)
        return (long_name,)

    def __get_names_from_pos_args(self, args):
        name = args['name']
        assert len(name) != 0, 'positional argument is empty'
        return (name,)

    def __get_kwargs_from_opt_args(self, args) -> dict:
        res = {}
        res['help'] = args['help']
        default = args['default']
        res['default'] = default
        if default is False:
            res['action'] = 'store_true'
            return res
        elif default is True:
            res['action'] = 'store_false'
            return res
        elif isinstance(default, int) or isinstance(default, str):
            res['action'] = 'store'
            res['nargs'] = '?'
            return res
        elif isinstance(default, list):
            res['action'] = 'extend'
            res['nargs'] = '*'
            return res
        else:
            assert False, f'type {type(default)} is not support'

    def __get_kwargs_from_pos_args(self, args) -> dict:
        res = {}
        res['help'] = args['help']
        res['default'] = args['default']
        res['nargs'] = '?'
        return res

    def __cast_opt_argv(self, opt_argv: list) -> list:
        self.opt_argv = []
        self.pos_argv = []
        self.__short_long_map = {}
        for args in opt_argv:
            if len(args) == 5:
                self.opt_argv.append(
                    dict(
                        sname=args[0],
                        lname=args[1],
                        help=args[2],
                        default=args[3],
                        required=args[4]
                    )
                )
                if len(args[1]) > 0:
                    self.__short_long_map[args[0]] = args[1]
            elif len(args) == 3:
                self.pos_argv.append(
                    dict(
                        name=args[0],
                        help=args[1],
                        default=args[2],
                    )
                )

    def __init_argv(self, opt_argv):
        for i in range(len(opt_argv)):
            if len(opt_argv[i]) == 5:
                while opt_argv[i][0].startswith('-'):
                    tmp = list(opt_argv[i])
                    tmp[0] = tmp[0][1:]
                    opt_argv[i] = tuple(tmp)
                while opt_argv[i][1].startswith('-'):
                    tmp = list(opt_argv[i])
                    tmp[1] = tmp[1][1:]
                    opt_argv[i] = tuple(tmp)

    def __init__(self, opt_argv=[], enable_plugin=False, plugin_dir='cmds') -> None:
        super().__init__(prog='argparse base')
        parser = argparse.ArgumentParser()
        if enable_plugin:
            self.plugin_dir = plugin_dir
            parser.add_argument('plugin', default=None,
                                nargs='?', help='<plugin>_ext.py')
            args = parser.parse_args()
            if getattr(args, 'plugin'):
                self.__skip_into_plugin(args.plugin)

        self.__init_argv(opt_argv)
        self.__cast_opt_argv(opt_argv)

        for args in self.opt_argv:
            self.add_argument(
                *self.__get_names_from_opt_args(args),
                **self.__get_kwargs_from_opt_args(args)
            )

        for args in self.pos_argv:
            self.add_argument(
                *self.__get_names_from_pos_args(args),
                **self.__get_kwargs_from_pos_args(args)
            )

        self.args = self.parse_args()

    def getopt(self, opt):
        return self.get_opt(opt)

    def get_opt(self, opt):
        if opt in self.__short_long_map:
            return getattr(self.args, self.__short_long_map[opt], None)
        return getattr(self.args, opt, None)

    def hasopt(self, opt):
        return self.sys_has_opt(opt)

    def sys_has_opt(self, opt):
        if opt in self.__short_long_map:
            return getattr(self.args, self.__short_long_map[opt], None) == None
        return getattr(self.args, opt, None) == None
