class AptMirrorConfig:
    """APT 镜像源配置"""

    MIRROR_URL: str = "https://mirrors.tuna.tsinghua.edu.cn/debian/"


class PipMirrorConfig:
    """Pip 镜像源配置"""

    MIRROR_URL: str = "https://pypi.tuna.tsinghua.edu.cn/simple/"
    TRUSTED_HOST: str = "pypi.tuna.tsinghua.edu.cn"


class DockerMirrorConfig:
    """Docker 镜像源配置"""

    MIRROR_URLS: list[str] = [
        "https://docker.1panel.live",
    ]
