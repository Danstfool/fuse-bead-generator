"""
拼豆图纸转换器
主程序入口
"""
import sys
import os

# 添加当前目录到路径
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, base_dir)

from gui_pyqt import main

if __name__ == "__main__":
    main()