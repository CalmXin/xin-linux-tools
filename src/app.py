from typer import Typer

from src.commands.mirror_command import mirror_app
from src.commands.repl_command import repl_app

main_app = Typer()

main_app.add_typer(mirror_app, name='mirror', help='替换镜像源')
main_app.add_typer(repl_app, name='')
