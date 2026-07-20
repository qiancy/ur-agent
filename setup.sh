#!/bin/bash
echo "==> 安装Python依赖..."
pip3 install -r requirements.txt

echo "==> 初始化数据库..."
python3 scripts/init_db.py
echo "==> 环境准备完成"