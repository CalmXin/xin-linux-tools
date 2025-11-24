from typer import Typer

from src.commands.mirror_command import mirror_app

main_app = Typer()

main_app.add_typer(mirror_app, name='mirror', help='替换镜像源')
