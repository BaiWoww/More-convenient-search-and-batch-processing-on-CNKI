"""
CNKI Desktop - 状态面板
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QProgressBar, QGroupBox,
)
from PySide6.QtCore import Signal, Qt, Slot


class StatusPanel(QGroupBox):
    """进度与日志面板"""

    def __init__(self, parent=None):
        super().__init__("运行状态", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # 进度条
        progress_row = QHBoxLayout()
        self.progress_label = QLabel("就绪")
        self.progress_label.setObjectName("statusLabel")
        progress_row.addWidget(self.progress_label)

        progress_row.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(300)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        progress_row.addWidget(self.progress_bar)

        layout.addLayout(progress_row)

        # 日志
        self.log_text = QTextEdit()
        self.log_text.setObjectName("logView")
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(180)
        layout.addWidget(self.log_text)

    @Slot(str)
    def append_log(self, message: str):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @Slot(str)
    def append_error(self, message: str):
        """添加错误日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f'<span style="color:#f38ba8">[{timestamp}] 错误: {message}</span>')
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @Slot(int, int)
    def update_progress(self, current: int, total: int):
        """更新进度"""
        if total > 0:
            pct = int(current * 100 / total)
            self.progress_bar.setValue(pct)
            self.progress_label.setText(f"{current}/{total}")
        else:
            self.progress_bar.setValue(0)
            self.progress_label.setText("就绪")

    def reset_progress(self):
        """重置进度"""
        self.progress_bar.setValue(0)
        self.progress_label.setText("就绪")

    def set_status(self, text: str):
        """设置状态文本"""
        self.progress_label.setText(text)
