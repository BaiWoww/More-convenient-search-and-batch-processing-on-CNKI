"""
CNKI Desktop - 浏览器设置对话框
首次运行时引导用户启动浏览器并登录CNKI
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QProgressBar,
)
from PySide6.QtCore import Signal, Qt


class BrowserSetupDialog(QDialog):
    """浏览器初始化引导对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("浏览器设置")
        self.setFixedSize(500, 360)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 标题
        title = QLabel("初始化浏览器")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0969da;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 说明
        desc = QLabel(
            "本工具需要使用 Chromium 浏览器来访问知网。\n"
            "点击【启动浏览器】后，将会弹出一个浏览器窗口。\n\n"
            "如果需要进行论文下载，请在弹出的浏览器窗口中\n"
            "登录您的知网账号（机构登录或个人登录均可）。\n\n"
            "登录状态会自动保存，下次使用无需重新登录。"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #57606a; font-size: 13px; line-height: 1.6;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        # 进度
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # 不确定模式
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # 状态
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 13px; color: #2da44e;")
        layout.addWidget(self.status_label)

        # 按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.launch_btn = QPushButton("启动浏览器")
        self.launch_btn.setObjectName("primaryBtn")
        self.launch_btn.setMinimumWidth(120)
        self.launch_btn.setMinimumHeight(36)
        self.launch_btn.clicked.connect(self._on_launch)
        btn_row.addWidget(self.launch_btn)

        self.skip_btn = QPushButton("稍后设置")
        self.skip_btn.setMinimumWidth(100)
        self.skip_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.skip_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addStretch()

    def _on_launch(self):
        self.launch_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.status_label.setText("正在启动浏览器...")
        self.accept()  # 关闭对话框，由主窗口处理启动

    def set_status(self, text: str, success: bool = True):
        self.status_label.setText(text)
        color = "#2da44e" if success else "#cf222e"
        self.status_label.setStyleSheet(f"color: {color}; font-size: 13px;")
        self.progress.setVisible(False)
        self.launch_btn.setEnabled(True)
        self.skip_btn.setEnabled(True)
