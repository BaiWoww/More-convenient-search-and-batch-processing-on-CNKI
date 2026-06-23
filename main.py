"""
CNKI论文检索助手 - 入口文件
"""
import sys
import os

# 确保项目根目录在 sys.path 中
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# Windows Unicode 修复
if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr and sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from cnki_desktop.app import MainWindow
from cnki_desktop.styles import MAIN_STYLE


def main():
    # 高DPI支持
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("CNKI论文检索助手")
    app.setApplicationDisplayName("CNKI论文检索助手")

    # 应用全局样式
    app.setStyleSheet(MAIN_STYLE)

    # 设置默认字体
    from PySide6.QtGui import QFont
    font = QFont("微软雅黑", 10)
    app.setFont(font)

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
