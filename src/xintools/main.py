from typer import Typer

from xintools.commands.mirror_command import mirror_app
from xintools.commands.repl_command import repl_app

main_app = Typer()

main_app.add_typer(mirror_app, name='mirror', help='替换镜像源')
main_app.add_typer(repl_app, name='')


def main() -> None:
    main_app()


if __name__ == '__main__':
    main()
