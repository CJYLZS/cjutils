
import sys
from cjutils.cmd import cmd_base


class cmd(cmd_base):
    def __init__(self) -> None:
        super().__init__([
        ], brief_intro="cmd base", enable_plugins=True)

    def main(self):

        return 0


if __name__ == "__main__":
    sys.exit(cmd().main())
