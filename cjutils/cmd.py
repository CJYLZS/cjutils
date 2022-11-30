import os
import sys
sys.path.append(os.path.realpath(os.path.dirname(__file__)))
import argparse


class cmd_base(argparse.ArgumentParser):
    def __skip_into_plugin(self, plugin):
        if self.plugin_dir not in sys.path:
            sys.path.append(self.plugin_dir)
        plugin_mod = f'{plugin}_ext'
        plugin_py = os.path.join(self.plugin_dir, f'{plugin_mod}.py')
        assert os.path.exists(
            plugin_py), f'{os.path.realpath(plugin_py)} not exist!'
        sys.argv.remove(plugin)
        ext = __import__(plugin_mod)
        sys.exit(ext.cmd().main())

    def __print_error(self, info):
        print(info)
        sys.exit(255)

    def __get_help_info(self, args):
        pass

    def __get_names_from_opt_args(self, args):
        short_name, long_name = args['sname'], args['lname']
        assert not (len(short_name) == 0 and len(long_name)
                    == 0), 'both short and long name is empty!'
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
                while opt_argv[i][0].startswith('-'):
                    tmp = list(opt_argv[i])
                    tmp[0] = tmp[0][1:]
                    opt_argv[i] = tuple(tmp)
                while opt_argv[i][1].startswith('-'):
                    tmp = list(opt_argv[i])
                    tmp[1] = tmp[1][1:]
                    opt_argv[i] = tuple(tmp)

    def __init__(self, options_argv=[], enable_plugins=False, plugin_dir='cmds', **kwargs) -> None:
        opt_argv = options_argv
        super().__init__(prog='argparse_base')

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
            self.plugin_dir = os.path.realpath(plugin_dir)
            self.add_argument('plugin', default=None,
                              nargs='?', help=os.path.join(plugin_dir, '<plugin>_ext.py'))
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
