"""
CNKI Desktop - 导出面板
"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QComboBox, QPushButton, QLineEdit,
    QFileDialog, QGroupBox, QGridLayout,
)
from PySide6.QtCore import Signal, Qt


class ExportPanel(QGroupBox):
    """导出控制面板"""

    export_clicked = Signal(dict)  # {output_dir, options}

    def __init__(self, parent=None):
        super().__init__("导出设置", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 导出内容选择
        content_row = QHBoxLayout()
        content_row.addWidget(QLabel("导出内容:"))

        self.chk_titles = QCheckBox("篇名")
        self.chk_titles.setChecked(True)
        content_row.addWidget(self.chk_titles)

        self.chk_citations = QCheckBox("引文 (GB/T 7714)")
        self.chk_citations.setChecked(True)
        content_row.addWidget(self.chk_citations)

        self.chk_abstracts = QCheckBox("摘要")
        self.chk_abstracts.setChecked(False)
        content_row.addWidget(self.chk_abstracts)

        self.chk_pdfs = QCheckBox("PDF原文")
        self.chk_pdfs.setChecked(False)
        content_row.addWidget(self.chk_pdfs)

        content_row.addStretch()
        layout.addLayout(content_row)

        # 格式选择
        format_grid = QGridLayout()
        format_grid.setSpacing(8)

        format_grid.addWidget(QLabel("篇名格式:"), 0, 0)
        self.fmt_titles = QComboBox()
        self.fmt_titles.addItems(["TXT", "XLSX"])
        self.fmt_titles.setFixedWidth(80)
        format_grid.addWidget(self.fmt_titles, 0, 1)

        format_grid.addWidget(QLabel("引文格式:"), 0, 2)
        self.fmt_citations = QComboBox()
        self.fmt_citations.addItems(["TXT", "DOCX"])
        self.fmt_citations.setFixedWidth(80)
        format_grid.addWidget(self.fmt_citations, 0, 3)

        format_grid.addWidget(QLabel("摘要格式:"), 0, 4)
        self.fmt_abstracts = QComboBox()
        self.fmt_abstracts.addItems(["TXT", "DOCX"])
        self.fmt_abstracts.setFixedWidth(80)
        format_grid.addWidget(self.fmt_abstracts, 0, 5)

        format_grid.setColumnStretch(6, 1)
        layout.addLayout(format_grid)

        # 输出目录
        dir_row = QHBoxLayout()
        dir_row.addWidget(QLabel("输出目录:"))
        self.dir_input = QLineEdit()
        default_dir = os.path.join(os.path.expanduser("~"), "Documents", "CNKI_Papers")
        self.dir_input.setText(default_dir)
        self.dir_input.setPlaceholderText("选择输出目录...")
        dir_row.addWidget(self.dir_input, 1)

        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(self.browse_btn)

        self.export_btn = QPushButton("导出选中项")
        self.export_btn.setObjectName("primaryBtn")
        self.export_btn.setMinimumWidth(100)
        self.export_btn.clicked.connect(self._on_export)
        dir_row.addWidget(self.export_btn)

        layout.addLayout(dir_row)

    def _browse_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择输出目录", self.dir_input.text()
        )
        if dir_path:
            self.dir_input.setText(dir_path)

    def _on_export(self):
        output_dir = self.dir_input.text().strip()
        if not output_dir:
            return

        options = {
            "titles": self.chk_titles.isChecked(),
            "titles_format": self.fmt_titles.currentText().lower(),
            "citations": self.chk_citations.isChecked(),
            "citations_format": self.fmt_citations.currentText().lower(),
            "abstracts": self.chk_abstracts.isChecked(),
            "abstracts_format": self.fmt_abstracts.currentText().lower(),
            "pdfs": self.chk_pdfs.isChecked(),
        }

        # 至少选一项
        if not any([options["titles"], options["citations"],
                    options["abstracts"], options["pdfs"]]):
            return

        self.export_clicked.emit({"output_dir": output_dir, "options": options})

    def get_output_dir(self) -> str:
        """获取输出目录"""
        return self.dir_input.text().strip()

    def wants_pdfs(self) -> bool:
        """是否需要下载PDF"""
        return self.chk_pdfs.isChecked()
