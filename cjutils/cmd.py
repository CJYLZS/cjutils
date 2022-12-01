import os
import sys
sys.path.append(os.path.realpath(os.path.dirname(__file__)))
import argparse


class cmd_base(argparse.ArgumentParser):
    def __skip_into_plugin(self, plugin):
        if self.plugins_dir not in sys.path:
            sys.path.append(self.plugins_dir)
        plugin_mod = f'{plugin}_ext'
        plugin_py = os.path.join(self.plugins_dir, f'{plugin_mod}.py')
        plugin_name = plugin_py[:-7]
        assert os.path.exists(
            plugin_py), f'{os.path.realpath(plugin_py)} not exist!'
        sys.argv.remove(plugin)
        sys.argv[0] = plugin_name
        ext = __import__(plugin_mod)
        sys.exit(ext.cmd(prog=plugin).main())

    def __print_error(self, info):
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
        elif isinstance(default, int) or isinstance(default, str) or isinstance(default, float):
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
                tmp = list(opt_argv[i])
                while tmp[0].startswith('-'):
                    tmp[0] = tmp[0][1:]
                while tmp[1].startswith('-'):
                    tmp[1] = tmp[1][1:]
                tmp[0] = tmp[0].replace('-', '_')
                tmp[1] = tmp[1].replace('-', '_')
                opt_argv[i] = tuple(tmp)

    class CustomHelpFormatter(argparse.HelpFormatter):
        def _get_builtin(self, key):
            return __builtins__.get(key, None)

        def _get_plugin_description(self) -> str:
            if not self._get_builtin('enable_plugins'):
                return ''
            plugins_list = []
            path = self._get_builtin('plugins_dir')
            if os.path.exists(path):
                for f in os.scandir(path):
                    if f.name.endswith('_ext.py'):
                        plugins_list.append(f.name[:-7])
            if len(plugins_list) == 0:
                return ''
            tmp = "\n\t".join(plugins_list)
            return f'plugins:\n\t{tmp}\n'

        def _format_usage(self, *args) -> str:
            text = super()._format_usage(*args)
            return text + f'{self._get_plugin_description()}'

    def _set_builtin(self, key, value):
        __builtins__[key] = value

    def _unset_builtin(self, key):
        if key in __builtins__:
            del __builtins__[key]

    def __init__(self, options_argv=[], enable_plugins=False, plugins_dir='cmds', prog=None, **kwargs) -> None:
        opt_argv = options_argv
        if enable_plugins:
            self.plugins_dir = os.path.join(os.path.dirname(
                os.path.realpath(sys.argv[0])), plugins_dir)
            self._set_builtin('enable_plugins', str(enable_plugins))
            self._set_builtin('plugins_dir', self.plugins_dir)
        else:
            self._unset_builtin('enable_plugins')
            self._unset_builtin('plugins_dir')

        super().__init__(prog=prog, formatter_class=self.CustomHelpFormatter)

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

        if enable_plugins and len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
            self.add_argument('plugin', default=None,
                              nargs='?', help=os.path.join(plugins_dir, '<plugin>_ext.py'))
            self.args = self.parse_args(args=sys.argv[1:2])
            if getattr(self.args, 'plugin', None):
                self.__skip_into_plugin(self.args.plugin)
            assert False, 'impossible'
        else:
            self.args = self.parse_args()

    def getopt(self, opt):
        return self.get_opt(opt)

    def get_opt(self, opt):
        if opt in self.__short_long_map:
            return getattr(self.args, self.__short_long_map[opt], None)
        return getattr(self.args, opt, None)


if __name__ == '__main__':
    class cmd(cmd_base):
        def __init__(self, options_argv=[], enable_plugins=False, plugins_dir='cmds', **kwargs) -> None:
            super().__init__(options_argv=[
                ('a', 'aa', 'aaa', False, False),
            ], enable_plugins=True)

    cmd().print_help()
