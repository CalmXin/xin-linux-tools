## 1. 背景

这个 CLI 工具主要是整合一些常用操作

## 2. 用法

### 2.1 下载项目

```bash
git clone https://github.com/CalmXin/xin-linux-tools.git
```



### 2.2 安装 Pyenv（可选）

```bash
# 当前在下载后的目录下
bash scripts/setup_pyenv.sh
```



### 2.3 执行

```bash
# 安装
bash scripts/setup.sh

# 运行指令
bash bin/xintools --help

# 或者
export PATH=$PWD/bin:$PATH
xintools --help
```

