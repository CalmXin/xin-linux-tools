import cmd
import sys
from typing import IO

from typer import Typer, echo

repl_app = Typer()


@repl_app.command()
def repl() -> None:
    """进入 REPL 模式"""

    from app.application import main_app

    try:
        import readline  # 支持方向键和历史记录（可选）

    except ImportError:
        pass

    typer_repl = TyperREPL()
    typer_repl.setup(main_app)
    typer_repl.cmdloop()


class TyperREPL(cmd.Cmd):
    intro = "Typer REPL mode. Type commands like: mirror list, config key value\nType 'exit' to quit."
    prompt = ">>> "

    def __init__(self, completekey: str = "tab", stdin: IO[str] | None = None, stdout: IO[str] | None = None):
        super().__init__(completekey, stdin, stdout)
        self.app = None

    def setup(self, app: Typer) -> None:
        self.app = app

    # ----- 指令区 -----

    @staticmethod
    def do_exit(arg):
        """Exit REPL."""

        return True

    @staticmethod
    def do_EOF(arg):
        echo("\nGoodbye!")
        return True

    def default(self, line: str):
        if line.strip() in ("exit", "quit"):
            return None

        if not line.strip():
            return None

        # 拆分命令并调用 Typer
        args = line.split()
        self._call_typer_command(args)
        return None

    def _call_typer_command(self, args: list[str]):
        """模拟命令行调用 Typer app"""

        # 临时替换 sys.argv
        original_argv = sys.argv

        try:
            sys.argv = ["main.py"] + args
            self.app()

        except SystemExit as e:
            # Typer 内部会 sys.exit(0) 或 (1)，我们忽略它以保持 REPL 运行
            if e.code != 0:
                echo(f"Command failed with exit code {e.code}", err=True)

        finally:
            sys.argv = original_argv
