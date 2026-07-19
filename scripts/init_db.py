# 初始化数据库脚本

import os
import sys
from src.db.database import init_database

def main():
    print("正在初始化数据库...")
    try:
        init_database()
        print("数据库初始化成功！")
    except Exception as e:
        print(f"数据库初始化失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()