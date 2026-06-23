"""
CNKI Desktop - 样式表
"""

MAIN_STYLE = """
QMainWindow {
    background-color: #f5f7fa;
}

QWidget#centralWidget {
    background-color: #f5f7fa;
}

/* 搜索面板 */
QGroupBox {
    font-weight: bold;
    font-size: 13px;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    background-color: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #1a1a2e;
}

/* 输入框 */
QLineEdit {
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
    background-color: #ffffff;
    selection-background-color: #0969da;
}
QLineEdit:focus {
    border: 2px solid #0969da;
}

/* 下拉框 */
QComboBox {
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
    background-color: #ffffff;
    min-width: 80px;
}
QComboBox:focus {
    border: 2px solid #0969da;
}
QComboBox::drop-down {
    border: none;
    width: 30px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #57606a;
    margin-right: 10px;
}
QComboBox QAbstractItemView {
    border: 1px solid #d0d7de;
    background-color: #ffffff;
    selection-background-color: #0969da;
    selection-color: #ffffff;
}

/* 按钮 - 主要 */
QPushButton {
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 13px;
    background-color: #f6f8fa;
    color: #24292f;
    min-height: 24px;
}
QPushButton:hover {
    background-color: #f3f4f6;
    border-color: #0969da;
}
QPushButton:pressed {
    background-color: #eaeef2;
}

/* 主要按钮 */
QPushButton#primaryBtn {
    background-color: #2da44e;
    color: #ffffff;
    border: 1px solid #1a7f37;
    font-weight: bold;
}
QPushButton#primaryBtn:hover {
    background-color: #2c974b;
}
QPushButton#primaryBtn:pressed {
    background-color: #298e46;
}

/* 危险按钮 */
QPushButton#dangerBtn {
    background-color: #cf222e;
    color: #ffffff;
    border: 1px solid #a40e26;
}
QPushButton#dangerBtn:hover {
    background-color: #a40e26;
}

/* 表格 */
QTableWidget {
    border: 1px solid #d0d7de;
    border-radius: 6px;
    background-color: #ffffff;
    gridline-color: #e8ecf0;
    font-size: 12px;
    selection-background-color: #ddf4ff;
    selection-color: #24292f;
}
QTableWidget::item {
    padding: 4px 8px;
}
QTableWidget::item:selected {
    background-color: #ddf4ff;
}
QHeaderView::section {
    background-color: #f6f8fa;
    border: 1px solid #d0d7de;
    padding: 6px 8px;
    font-weight: bold;
    font-size: 12px;
    color: #57606a;
}

/* 进度条 */
QProgressBar {
    border: 1px solid #d0d7de;
    border-radius: 6px;
    text-align: center;
    font-size: 12px;
    background-color: #e8ecf0;
    min-height: 20px;
}
QProgressBar::chunk {
    background-color: #2da44e;
    border-radius: 5px;
}

/* 日志文本框 */
QTextEdit#logView {
    border: 1px solid #d0d7de;
    border-radius: 6px;
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
    padding: 8px;
}

/* 复选框 */
QCheckBox {
    font-size: 13px;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #d0d7de;
    border-radius: 4px;
    background-color: #ffffff;
}
QCheckBox::indicator:checked {
    background-color: #0969da;
    border-color: #0969da;
}
QCheckBox::indicator:hover {
    border-color: #0969da;
}

/* SpinBox */
QSpinBox {
    border: 1px solid #d0d7de;
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 13px;
    background-color: #ffffff;
}
QSpinBox:focus {
    border: 2px solid #0969da;
}

/* 标签 */
QLabel {
    font-size: 13px;
    color: #24292f;
}
QLabel#titleLabel {
    font-size: 18px;
    font-weight: bold;
    color: #0969da;
}
QLabel#statusLabel {
    font-size: 12px;
    color: #57606a;
    padding: 2px 8px;
}

/* 状态栏 */
QStatusBar {
    background-color: #f6f8fa;
    border-top: 1px solid #d0d7de;
    font-size: 12px;
    color: #57606a;
}

/* 菜单栏 */
QMenuBar {
    background-color: #f6f8fa;
    border-bottom: 1px solid #d0d7de;
}
QMenuBar::item {
    padding: 6px 12px;
}
QMenuBar::item:selected {
    background-color: #0969da;
    color: #ffffff;
}
QMenu {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
}
QMenu::item {
    padding: 6px 24px;
}
QMenu::item:selected {
    background-color: #0969da;
    color: #ffffff;
}

/* 滚动条 */
QScrollBar:vertical {
    background: #f6f8fa;
    width: 12px;
    border: none;
}
QScrollBar::handle:vertical {
    background: #c1c8cf;
    border-radius: 6px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #8b949e;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* 工具提示 */
QToolTip {
    background-color: #24292f;
    color: #ffffff;
    border: none;
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 12px;
}
"""
