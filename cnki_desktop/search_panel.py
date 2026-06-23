"""
CNKI Desktop - 搜索面板
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QLineEdit, QComboBox, QSpinBox, QPushButton, QGroupBox,
)
from PySide6.QtCore import Signal, Qt

from core.config import SEARCH_FIELD_NAMES, SEARCH_FIELDS, DATABASE_NAMES, DATABASE_CLASSIDS


class SearchPanel(QGroupBox):
    """搜索控制面板"""

    search_clicked = Signal(dict)  # {keyword, field, classid, max_pages}
    stop_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__("检索条件", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 第一行: 搜索类型 + 数据库
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        row1.addWidget(QLabel("搜索类型:"))
        self.field_combo = QComboBox()
        self.field_combo.addItems(SEARCH_FIELD_NAMES)
        self.field_combo.setCurrentIndex(0)  # 默认 "主题"
        self.field_combo.setFixedWidth(100)
        row1.addWidget(self.field_combo)

        row1.addSpacing(16)
        row1.addWidget(QLabel("数据库:"))
        self.db_combo = QComboBox()
        self.db_combo.addItems(DATABASE_NAMES)
        self.db_combo.setCurrentIndex(0)  # 默认 "学术期刊"
        self.db_combo.setFixedWidth(110)
        row1.addWidget(self.db_combo)

        row1.addStretch()
        layout.addLayout(row1)

        # 第二行: 关键词 + 页数 + 按钮
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        row2.addWidget(QLabel("关键词:"))
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("输入搜索关键词，如: 恩诺沙星 药代动力学")
        self.keyword_input.setMinimumWidth(300)
        self.keyword_input.returnPressed.connect(self._on_search)
        row2.addWidget(self.keyword_input, 1)

        row2.addWidget(QLabel("最大页数:"))
        self.pages_spin = QSpinBox()
        self.pages_spin.setRange(1, 50)
        self.pages_spin.setValue(3)
        self.pages_spin.setFixedWidth(65)
        row2.addWidget(self.pages_spin)

        self.search_btn = QPushButton("搜索")
        self.search_btn.setObjectName("primaryBtn")
        self.search_btn.setMinimumWidth(80)
        self.search_btn.clicked.connect(self._on_search)
        row2.addWidget(self.search_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setObjectName("dangerBtn")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop)
        row2.addWidget(self.stop_btn)

        layout.addLayout(row2)

    def _on_search(self):
        keyword = self.keyword_input.text().strip()
        if not keyword:
            return

        field_name = self.field_combo.currentText()
        db_name = self.db_combo.currentText()

        params = {
            "keyword": keyword,
            "field": SEARCH_FIELDS.get(field_name, "SU"),
            "classid": DATABASE_CLASSIDS.get(db_name, "YSTT4HG0"),
            "max_pages": self.pages_spin.value(),
        }
        self.search_clicked.emit(params)
        self.set_searching(True)

    def _on_stop(self):
        self.stop_clicked.emit()

    def set_searching(self, searching: bool):
        """切换搜索中/空闲状态"""
        self.search_btn.setEnabled(not searching)
        self.stop_btn.setEnabled(searching)
        self.keyword_input.setEnabled(not searching)
        self.field_combo.setEnabled(not searching)
        self.db_combo.setEnabled(not searching)
        self.pages_spin.setEnabled(not searching)

    def get_params(self) -> dict:
        """获取当前搜索参数"""
        field_name = self.field_combo.currentText()
        db_name = self.db_combo.currentText()
        return {
            "keyword": self.keyword_input.text().strip(),
            "field": SEARCH_FIELDS.get(field_name, "SU"),
            "classid": DATABASE_CLASSIDS.get(db_name, "YSTT4HG0"),
            "max_pages": self.pages_spin.value(),
        }
