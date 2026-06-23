"""
CNKI Desktop - 搜索结果表格
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QLabel,
    QAbstractItemView, QGroupBox, QCheckBox,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor

from core.api import Paper


class ResultsTable(QGroupBox):
    """搜索结果表格组件"""

    fetch_details_clicked = Signal(list)  # 请求获取选中论文的详情
    download_pdf_clicked = Signal(list)   # 请求下载选中论文的PDF

    def __init__(self, parent=None):
        super().__init__("搜索结果", parent)
        self._papers = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # 工具栏
        toolbar = QHBoxLayout()

        self.count_label = QLabel("共 0 篇论文")
        self.count_label.setObjectName("statusLabel")
        toolbar.addWidget(self.count_label)

        toolbar.addStretch()

        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self._select_all)
        toolbar.addWidget(self.select_all_btn)

        self.invert_btn = QPushButton("反选")
        self.invert_btn.clicked.connect(self._invert_selection)
        toolbar.addWidget(self.invert_btn)

        self.deselect_btn = QPushButton("取消全选")
        self.deselect_btn.clicked.connect(self._deselect_all)
        toolbar.addWidget(self.deselect_btn)

        toolbar.addSpacing(20)

        self.detail_btn = QPushButton("获取详情")
        self.detail_btn.clicked.connect(self._on_fetch_details)
        self.detail_btn.setEnabled(False)
        toolbar.addWidget(self.detail_btn)

        self.download_btn = QPushButton("下载PDF")
        self.download_btn.setObjectName("primaryBtn")
        self.download_btn.clicked.connect(self._on_download_pdfs)
        self.download_btn.setEnabled(False)
        toolbar.addWidget(self.download_btn)

        layout.addLayout(toolbar)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "", "#", "篇名", "作者", "刊名", "年份", "被引", "状态"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)

        # 列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 36)   # 复选框列
        self.table.setColumnWidth(1, 40)   # 序号
        self.table.setColumnWidth(3, 150)  # 作者
        self.table.setColumnWidth(4, 130)  # 刊名
        self.table.setColumnWidth(5, 55)   # 年份
        self.table.setColumnWidth(6, 55)   # 被引
        self.table.setColumnWidth(7, 80)   # 状态

        layout.addWidget(self.table)

    def populate(self, papers: list):
        """填充搜索结果到表格"""
        self._papers = papers
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(papers))

        for row, paper in enumerate(papers):
            # 复选框
            chk = QCheckBox()
            chk.stateChanged.connect(lambda state, r=row: self._on_checkbox_changed(r, state))
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.addWidget(chk)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, widget)

            # 序号
            item = QTableWidgetItem(str(row + 1))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, item)

            # 篇名
            item = QTableWidgetItem(paper.title[:100])
            item.setToolTip(paper.title)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, item)

            # 作者
            authors_str = ", ".join(paper.authors[:3])
            if len(paper.authors) > 3:
                authors_str += " 等"
            item = QTableWidgetItem(authors_str)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, item)

            # 刊名
            item = QTableWidgetItem(paper.journal)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 4, item)

            # 年份
            item = QTableWidgetItem(paper.year)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 5, item)

            # 被引
            item = QTableWidgetItem(paper.cited_count)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 6, item)

            # 状态
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 7, item)

        self.table.setSortingEnabled(True)
        self.count_label.setText(f"共 {len(papers)} 篇论文")
        self._update_buttons()

    def update_row(self, row: int, paper: Paper):
        """更新单行数据"""
        if row >= self.table.rowCount():
            return

        # 更新摘要信息
        if paper.abstract:
            authors_str = ", ".join(paper.authors[:3])
            if len(paper.authors) > 3:
                authors_str += " 等"
            self.table.item(row, 3).setText(authors_str)

        # 更新状态
        status = ""
        if paper.pdf_downloaded:
            status = "已下载"
        elif paper.detail_fetched:
            status = "已获取"
        self.table.item(row, 7).setText(status)

        # 更新内部数据
        if row < len(self._papers):
            self._papers[row] = paper

    def update_row_status(self, row: int, status: str, color: str = ""):
        """更新行状态"""
        if row < self.table.rowCount():
            item = self.table.item(row, 7)
            if item:
                item.setText(status)
                if color:
                    item.setForeground(QColor(color))

    def set_row_checked(self, row: int, checked: bool):
        """设置行复选框状态"""
        widget = self.table.cellWidget(row, 0)
        if widget:
            chk = widget.findChild(QCheckBox)
            if chk:
                chk.setChecked(checked)

    def get_selected_papers(self) -> list:
        """获取选中的论文列表"""
        selected = []
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if widget:
                chk = widget.findChild(QCheckBox)
                if chk and chk.isChecked():
                    if row < len(self._papers):
                        selected.append(self._papers[row])
        return selected

    def get_all_papers(self) -> list:
        """获取所有论文"""
        return self._papers

    def mark_downloaded(self, title: str):
        """标记论文为已下载"""
        for i, paper in enumerate(self._papers):
            if paper.title == title:
                paper.pdf_downloaded = True
                self.update_row_status(i, "已下载", "#2da44e")
                break

    def _on_checkbox_changed(self, row: int, state: int):
        """复选框状态改变"""
        if row < len(self._papers):
            self._papers[row].selected = (state == Qt.CheckState.Checked.value)
        self._update_buttons()

    def _update_buttons(self):
        """更新按钮状态"""
        selected = self.get_selected_papers()
        has_selection = len(selected) > 0
        self.detail_btn.setEnabled(has_selection)
        self.download_btn.setEnabled(has_selection)

    def _select_all(self):
        """全选"""
        for row in range(self.table.rowCount()):
            self.set_row_checked(row, True)

    def _invert_selection(self):
        """反选"""
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if widget:
                chk = widget.findChild(QCheckBox)
                if chk:
                    chk.setChecked(not chk.isChecked())

    def _deselect_all(self):
        """取消全选"""
        for row in range(self.table.rowCount()):
            self.set_row_checked(row, False)

    def _on_fetch_details(self):
        selected = self.get_selected_papers()
        if selected:
            self.fetch_details_clicked.emit(selected)

    def _on_download_pdfs(self):
        selected = self.get_selected_papers()
        if selected:
            self.download_pdf_clicked.emit(selected)
