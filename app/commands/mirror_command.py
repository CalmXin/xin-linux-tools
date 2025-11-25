import json
import os
import shutil
import subprocess
import textwrap
from pathlib import Path
from typing import Any

from typer import Typer

from app.core.config import AptMirrorConfig, DockerMirrorConfig, PipMirrorConfig
from app.core.logger import logger

mirror_app = Typer()


# ========== 指令区 ==========

@mirror_app.command()
def apt() -> None:
    """替换 apt 镜像源"""

    apt_mirror = AptMirror()
    apt_mirror.execute()


@mirror_app.command()
def pip() -> None:
    """替换 pip 镜像源"""

    pip_mirror = PipMirror()
    pip_mirror.execute()


@mirror_app.command()
def docker() -> None:
    """替换 Docker 镜像源"""

    docker_mirror = DockerMirror()
    docker_mirror.execute()


# ========== 逻辑区 ==========

class AptMirror:
    """替换 apt 镜像源"""

    # 备份原始 sources.list
    SOURCES_PATH = "/etc/apt/sources.list"
    BACKUP_PATH = "/etc/apt/sources.list.bak"

    def __init__(self):
        self._source_file_path = Path(self.SOURCES_PATH)
        self._backup_file_path = Path(self.BACKUP_PATH)
        self._mirror_url = AptMirrorConfig.MIRROR_URL

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
            deb {self._mirror_url} {version_codename} main contrib non-free non-free-firmware
            deb {self._mirror_url} {version_codename}-updates main contrib non-free non-free-firmware
            deb {self._mirror_url} {version_codename}-backports main contrib non-free non-free-firmware
            deb http://security.debian.org/debian-security {version_codename}-security main contrib non-free non-free-firmware
        """
        content = textwrap.dedent(_content).strip()

        try:
            Path(self._source_file_path).write_text(content)
            logger.info(f"已成功将 APT 源替换为：{self._mirror_url}")

        except PermissionError:
            logger.error("写入 sources.list 失败，请以 root 权限运行此脚本")


class PipMirror:
    """配置 pip 镜像源（优先清华源）"""

    def __init__(self, index_url: str | None = None, trusted_host: str | None = None) -> None:
        self._index_url = index_url or PipMirrorConfig.MIRROR_URL
        self._trusted_host = trusted_host or PipMirrorConfig.TRUSTED_HOST

    def execute(self) -> None:
        """执行 pip 镜像源配置"""

        config_path = self._get_config_path()
        self._write_config(config_path)

    @staticmethod
    def _get_config_path() -> Path:
        """获取 pip 配置文件路径"""

        return Path.home() / ".pip" / "pip.conf"

    def _generate_config_content(self) -> str:
        """生成 pip.conf 内容"""

        _str = f"""
            [global]
            index-url = {self._index_url}
            trusted-host = {self._trusted_host}
        """

        return textwrap.dedent(_str).strip()

    def _write_config(self, path: Path) -> None:
        """写入 pip 配置文件"""

        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            f.write(self._generate_config_content())

        logger.info("pip 镜像源已配置")


class DockerMirror:
    """配置 Docker 镜像加速器（优先清华源）"""

    def __init__(self, mirrors: list[str] | None = None) -> None:
        self._mirrors = mirrors or DockerMirrorConfig.MIRROR_URLS

    def execute(self) -> None:
        """执行 Docker 镜像源配置"""

        config_path = self._get_config_path()
        config = self._read_existing_config(config_path)
        config["registry-mirrors"] = self._mirrors

        self._write_config(config_path, config)
        self._reload_docker_daemon()

    @staticmethod
    def _get_config_path() -> Path:
        """获取 Docker 配置文件路径"""

        return Path.home() / ".docker" / "daemon.json"

    @staticmethod
    def _read_existing_config(path: Path) -> dict[str, Any]:
        """读取现有 daemon.json 配置"""

        if not path.exists():
            return {}

        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)

        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"无法解析现有 Docker 配置 {path}，将覆盖：{e=}")
            return {}

    @staticmethod
    def _write_config(path: Path, config: dict[str, Any]) -> None:
        """写入新的 daemon.json"""

        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

        logger.info("Docker 镜像源已配置")

    @staticmethod
    def _reload_docker_daemon() -> None:
        """尝试重载 Docker 服务（仅 Linux systemd）"""

        try:
            result = subprocess.run(
                ["sudo", "systemctl", "is-active", "docker"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0 and "active" in result.stdout:
                subprocess.run(["sudo", "systemctl", "reload", "docker"], check=True)
                logger.info("已重载 Docker 服务")

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            # 忽略错误（如非 systemd 系统、无 sudo 权限等）
            logger.warning("无法重载 Docker 服务（可能非 systemd 系统或权限不足）")
