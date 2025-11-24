import os
import shutil
import subprocess
import textwrap
from pathlib import Path

from typer import Typer

from src.core.logger import logger

mirror_app = Typer()


# ========== 指令区 ==========

@mirror_app.command()
def apt() -> None:
    """替换系统 apt 镜像源"""

    apt_mirror = AptMirror()
    apt_mirror.execute()


# ========== 逻辑区 ==========

class AptMirror:
    """替换 apt 镜像源"""

    # 配置：选择镜像源（可替换为其他国内源，如阿里云、中科大等）
    MIRROR_URL = "https://mirrors.tuna.tsinghua.edu.cn/debian/"

    # 备份原始 sources.list
    SOURCES_PATH = "/etc/apt/sources.list"
    BACKUP_PATH = "/etc/apt/sources.list.bak"

    def __init__(self):
        self._source_file_path = Path(self.SOURCES_PATH)
        self._backup_file_path = Path(self.BACKUP_PATH)

    def execute(self) -> None:
        """执行函数"""

        if not self._is_root():
            logger.info("此脚本需要 root 权限，请使用 sudo 运行")

        self._backup_sources()
        self._replace_sources()
        logger.info("操作完成，请运行 'sudo apt update' 更新软件包列表。")

    @staticmethod
    def _is_root() -> bool:
        return os.geteuid() == 0

    def _backup_sources(self) -> None:
        if self._source_file_path.exists():
            shutil.copy(self._source_file_path, self._backup_file_path)
            logger.info(f"已备份原始 sources.list 到 {self._backup_file_path}")
        else:
            logger.warning(f"警告: {self._source_file_path} 不存在，跳过备份")

    def _replace_sources(self) -> None:
        # 获取 Debian 版本代号（如 bookworm, bullseye）
        try:
            os_release = Path('/etc/os-release').read_text()
            version_codename = None
            for line in os_release.splitlines():
                if line.startswith('VERSION_CODENAME='):
                    version_codename = line.split('=', 1)[1].strip()
                    break

            if not version_codename:
                # 如果 VERSION_CODENAME 不存在，尝试从 PRETTY_NAME 推断
                result = subprocess.run(['lsb_release', '-cs'], capture_output=True, text=True)
                if result.returncode == 0:
                    version_codename = result.stdout.strip()
                else:
                    logger.warning("无法自动获取 Debian 版本代号，请手动指定")
                    return None

        except Exception as e:
            logger.error(f"获取系统版本失败: {e=}")
            return None

        # 构建新的 sources.list 内容
        _content = f"""
            deb {self.MIRROR_URL} {version_codename} main contrib non-free non-free-firmware
            deb {self.MIRROR_URL} {version_codename}-updates main contrib non-free non-free-firmware
            deb {self.MIRROR_URL} {version_codename}-backports main contrib non-free non-free-firmware
            deb http://security.debian.org/debian-security {version_codename}-security main contrib non-free non-free-firmware
        """
        content = textwrap.dedent(_content).strip()

        try:
            Path(self._source_file_path).write_text(content)
            logger.info(f"已成功将 APT 源替换为：{self.MIRROR_URL}")

        except PermissionError:
            logger.error("写入 sources.list 失败，请以 root 权限运行此脚本")
