#!/bin/bash

set -e # 遇到错误立即退出

# --- 配置变量 ---
PYENV_ROOT="$HOME/.pyenv"

# --- 检测 Shell ---
detect_shell() {
    if [ -n "$SHELL" ]; then
        if echo "$SHELL" | grep -q "zsh"; then
            echo "zsh"
            return
        elif echo "$SHELL" | grep -q "bash"; then
            echo "bash"
            return
        fi
    fi
    # 如果 $SHELL 不明确，尝试从进程获取
    case $(ps -p "$PPID" -o comm= 2>/dev/null) in
        *zsh*) echo "zsh" ;;
        *bash*) echo "bash" ;;
        *) echo "unknown" ;;
    esac
}

# --- 安装必要的依赖 ---
install_build_dependencies() {
    echo "正在检测并安装必要的编译依赖..."

    # 检测发行版
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi

    echo "检测到的操作系统: $OS (Version: $VER)"

    # 根据不同的包管理器安装依赖
    if command -v apt-get &> /dev/null; then
        echo "检测到 apt 包管理器 (Debian/Ubuntu/WSL)..."
        # 检查当前用户是否可以无密码运行 sudo (避免脚本在此处卡住)
        if sudo -n true 2>/dev/null; then
            echo "使用 sudo 安装依赖..."
            sudo apt-get update
            sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \
                libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
                libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
                libffi-dev liblzma-dev git
        else
            echo "错误: 需要安装编译依赖，但当前用户无法执行 'sudo' 或需要输入密码。请手动运行以下命令："
            echo "sudo apt-get update && sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev git"
            exit 1
        fi
    elif command -v yum &> /dev/null; then
        echo "检测到 yum 包管理器 (CentOS/RHEL)..."
        if sudo -n true 2>/dev/null; then
            echo "使用 sudo 安装依赖..."
            sudo yum install -y gcc zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel tk-devel libffi-devel xz-devel git
        else
            echo "错误: 需要安装编译依赖，但当前用户无法执行 'sudo' 或需要输入密码。请手动运行以下命令："
            echo "sudo yum install -y gcc zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel tk-devel libffi-devel xz-devel git"
            exit 1
        fi
    elif command -v dnf &> /dev/null; then
        echo "检测到 dnf 包管理器 (Fedora)..."
        if sudo -n true 2>/dev/null; then
            echo "使用 sudo 安装依赖..."
            sudo dnf install -y gcc zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel tk-devel libffi-devel xz-devel git
        else
            echo "错误: 需要安装编译依赖，但当前用户无法执行 'sudo' 或需要输入密码。请手动运行以下命令："
            echo "sudo dnf install -y gcc zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel tk-devel libffi-devel xz-devel git"
            exit 1
        fi
    elif command -v apk &> /dev/null; then
        echo "检测到 apk 包管理器 (Alpine)..."
        if sudo -n true 2>/dev/null; then
            echo "使用 sudo 安装依赖..."
            sudo apk add --no-cache make build-base libffi-dev openssl-dev bzip2-dev readline-dev sqlite-dev xz-dev zlib-dev git
        else
            # 在 Alpine 中，通常 root 用户可以直接运行 apk
            echo "以 root 权限安装依赖..."
            apk add --no-cache make build-base libffi-dev openssl-dev bzip2-dev readline-dev sqlite-dev xz-dev zlib-dev git
        fi
    else
        echo "警告: 未能自动检测到 apt, yum, dnf 或 apk。请手动安装编译 Python 所需的依赖，如 build-essential, libssl-dev, zlib1g-dev 等。"
        echo "然后重新运行此脚本。"
        exit 1
    fi

    echo "编译依赖安装完成。"
}

# --- 安装 Pyenv ---
install_pyenv() {
    echo "开始安装 Pyenv..."
    if [ -d "$PYENV_ROOT" ]; then
        echo "警告: $PYENV_ROOT 目录已存在。如果要重新安装，请先手动删除该目录。"
        exit 1
    fi

    curl -fsSL https://pyenv.run | bash
    if [ $? -eq 0 ]; then
        echo "Pyenv 安装成功！"
    else
        echo "Pyenv 安装失败！请检查网络连接或手动安装。"
        exit 1
    fi
}

# --- 配置 Shell ---
configure_shell() {
    local shell_type="$1"
    local config_file=""

    case "$shell_type" in
        zsh)
            config_file="$HOME/.zshrc"
            ;;
        bash)
            config_file="$HOME/.bashrc"
            ;;
        *)
            echo "无法自动检测到 zsh 或 bash。请手动将以下行添加到你的 shell 配置文件中："
            echo "export PYENV_ROOT=\"\$HOME/.pyenv\""
            echo "export PATH=\"\$PYENV_ROOT/bin:\$PATH\""
            echo "eval \"\$(pyenv init -)\""
            exit 1
            ;;
    esac

    echo "正在配置 $shell_type (修改 $config_file)..."
    # 使用 grep 检查并追加配置，避免重复
    grep -qF 'export PYENV_ROOT="$HOME/.pyenv"' "$config_file" || echo 'export PYENV_ROOT="$HOME/.pyenv"' >> "$config_file"
    grep -qF 'export PATH="$PYENV_ROOT/bin:$PATH"' "$config_file" || echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> "$config_file"
    grep -qF 'eval "$(pyenv init -)"' "$config_file" || echo 'eval "$(pyenv init -)"' >> "$config_file"
    grep -qF 'export PYTHON_BUILD_MIRROR_URL=https://mirrors.tuna.tsinghua.edu.cn/python/' "$config_file" || echo 'export PYTHON_BUILD_MIRROR_URL=https://mirrors.tuna.tsinghua.edu.cn/python/' >> "$config_file"
    grep -qF 'export PYTHON_BUILD_MIRROR_URL_SKIP_CHECKSUM=1' "$config_file" || echo 'export PYTHON_BUILD_MIRROR_URL_SKIP_CHECKSUM=1' >> "$config_file"

    echo "Shell 配置已更新。请运行 'source $config_file' 或重新打开终端以使更改生效。"
}

# --- 主流程 ---
main() {
    shell_type=$(detect_shell)
    echo "检测到的 Shell: $shell_type"

    # 总是安装依赖，因为 Pyenv 安装 Python 时需要
    install_build_dependencies

    if [ ! -d "$PYENV_ROOT" ]; then
        install_pyenv
        configure_shell "$shell_type"
        echo "Pyenv 安装和配置完成。"
        echo "请运行 'source ~/.${shell_type}rc' 或重新打开终端以使更改生效。"
        echo "之后你就可以使用 'pyenv install <version>' 来安装具体的 Python 版本了。"
    else
        echo "Pyenv 已安装在 $PYENV_ROOT。"
        echo "请确保 Shell 配置已加载 (source ~/.${shell_type}rc)。"
        echo "你可以使用 'pyenv install <version>' 来安装新的 Python 版本。"
    fi
}

# --- 执行主流程 ---
main
