#!/bin/bash

set -e  # 遇到错误立即退出

# 获取当前脚本的真实绝对路径（自动处理软链接）
REAL_PATH=$(readlink -f "${BASH_SOURCE[0]}")
BASE_DIR=$(dirname "$(dirname "$REAL_PATH")")

cd "$BASE_DIR"

# 检查虚拟环境是否存在（默认使用 venv）
VENV_DIR="${BASE_DIR}/.linux_venv"

if [ ! -d "$VENV_DIR" ]; then
    # 检查 pyenv 是否存在
    if command -v pyenv &> /dev/null; then
        source "$HOME/.bashrc"
        pyenv local 3.11.9
        PYTHON_CMD="python"
    else
        PYTHON_CMD="python3"
    fi

    echo "Virtual environment not found. Creating one with $PYTHON_CMD..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    echo "Virtual environment created."

    # 激活虚拟环境
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"

    # 安装依赖（假设依赖在 requirements.txt 中）
    if [ -f "requirements.txt" ]; then
        echo "Installing dependencies from requirements.txt..."
        pip install -r requirements.txt
    else
        echo "No requirements.txt found. Skipping dependency installation."
    fi

    echo "Setup complete. Virtual environment is active."
    deactivate
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"
pip install -e .