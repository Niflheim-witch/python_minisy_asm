import sys
import os

# 将当前目录添加到路径，确保能找到 py_minisys_asm 包
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from py_minisys_asm.cli import main

if __name__ == '__main__':
    sys.exit(main())
