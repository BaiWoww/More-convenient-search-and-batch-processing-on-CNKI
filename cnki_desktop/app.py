"""
CNKI Desktop - 主窗口
整合所有面板和工作线程
"""
import os
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QMessageBox, QStatusBar, QMenuBar, QMenu,
    QFileDialog, QApplication,
)
from PySide6.QtCore import Qt, QThread, Slot
from PySide6.QtGui import QAction

from cnki_desktop.search_panel import SearchPanel
from cnki_desktop.results_table import ResultsTable
from cnki_desktop.export_panel import ExportPanel
from cnki_desktop.status_panel import StatusPanel
from cnki_desktop.styles import MAIN_STYLE
from cnki_desktop.browser_setup import BrowserSetupDialog
from cnki_desktop.workers import BrowserWorker, WorkerCommand, CommandType


class MainWindow(QMainWindow):
    """CNKI论文检索助手主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CNKI论文检索助手")
        self.setMinimumSize(1000, 750)
        self.resize(1200, 850)

        # 工作线程
        self._worker_thread = None
        self._worker = None
        self._is_searching = False
        self._is_downloading = False

        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()
        self._connect_signals()

        # 自动启动浏览器
        self._init_browser()

    def _setup_ui(self):
        """设置界面布局"""
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 12, 16, 8)
        layout.setSpacing(12)

        # 标题
        title_row = QHBoxLayout()
        title_label = QLabel("CNKI 论文检索助手")
        title_label.setObjectName("titleLabel")
        title_row.addWidget(title_label)
        title_row.addStretch()

        self.browser_status = QLabel("浏览器: 未连接")
        self.browser_status.setObjectName("statusLabel")
        title_row.addWidget(self.browser_status)
        layout.addLayout(title_row)

        # 搜索面板
        self.search_panel = SearchPanel()
        layout.addWidget(self.search_panel)

        # 结果表格
        self.results_table = ResultsTable()
        layout.addWidget(self.results_table, 1)  # 给表格最大空间

        # 导出面板
        self.export_panel = ExportPanel()
        layout.addWidget(self.export_panel)

        # 状态面板
        self.status_panel = StatusPanel()
        layout.addWidget(self.status_panel)

    def _setup_menu(self):
        """设置菜单栏"""
        menubar = self.menuBar()

        # 浏览器菜单
        browser_menu = menubar.addMenu("浏览器")

        self.action_launch = QAction("启动浏览器", self)
        self.action_launch.triggered.connect(self._init_browser)
        browser_menu.addAction(self.action_launch)

        self.action_close = QAction("关闭浏览器", self)
        self.action_close.triggered.connect(self._close_browser)
        self.action_close.setEnabled(False)
        browser_menu.addAction(self.action_close)

        browser_menu.addSeparator()

        self.action_refresh_session = QAction("刷新会话", self)
        self.action_refresh_session.triggered.connect(self._refresh_session)
        self.action_refresh_session.setEnabled(False)
        browser_menu.addAction(self.action_refresh_session)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        action_about = QAction("关于", self)
        action_about.triggered.connect(self._show_about)
        help_menu.addAction(action_about)

    def _setup_statusbar(self):
        """设置状态栏"""
        self.statusBar().showMessage("就绪")

    def _connect_signals(self):
        """连接信号和槽"""
        # 搜索面板
        self.search_panel.search_clicked.connect(self._on_search)
        self.search_panel.stop_clicked.connect(self._on_stop)

        # 结果表格
        self.results_table.fetch_details_clicked.connect(self._on_fetch_details)
        self.results_table.download_pdf_clicked.connect(self._on_download_pdfs)

        # 导出面板
        self.export_panel.export_clicked.connect(self._on_export)

    def _init_browser(self):
        """初始化浏览器工作线程"""
        if self._worker_thread and self._worker_thread.isRunning():
            return

        self._worker_thread = QThread()
        self._worker = BrowserWorker()
        self._worker.moveToThread(self._worker_thread)

        # 连接工作器信号
        self._worker.log.connect(self.status_panel.append_log)
        self._worker.error.connect(self.status_panel.append_error)
        self._worker.progress.connect(self.status_panel.update_progress)
        self._worker.search_done.connect(self._on_search_done)
        self._worker.details_done.connect(self._on_details_done)
        self._worker.download_done.connect(self._on_download_done)
        self._worker.download_batch_done.connect(self._on_download_batch_done)
        self._worker.export_done.connect(self._on_export_done)
        self._worker.captcha_required.connect(self._on_captcha)
        self._worker.browser_ready.connect(self._on_browser_ready)
        self._worker.session_status.connect(self._on_session_status)

        # 启动线程 - run() 会自动初始化浏览器
        self._worker_thread.started.connect(self._worker.run)
        self._worker_thread.start()

        self.statusBar().showMessage("正在启动浏览器...")

    def _close_browser(self):
        """关闭浏览器"""
        if self._worker:
            self._worker.post_command(WorkerCommand(CommandType.CLOSE_BROWSER))
            self._worker.request_stop()

        if self._worker_thread:
            self._worker_thread.quit()
            self._worker_thread.wait(5000)

        self._worker = None
        self._worker_thread = None
        self.browser_status.setText("浏览器: 未连接")
        self.action_launch.setEnabled(True)
        self.action_close.setEnabled(False)
        self.action_refresh_session.setEnabled(False)

    def _on_search(self, params: dict):
        """搜索按钮点击"""
        if not self._worker or not self._worker.is_browser_ready():
            QMessageBox.warning(self, "提示", "请先启动浏览器")
            return

        self._is_searching = True
        self.status_panel.reset_progress()
        self._worker.post_command(WorkerCommand(CommandType.SEARCH, params))

    def _on_stop(self):
        """停止按钮点击"""
        if self._worker:
            self._worker.request_stop()
        self.search_panel.set_searching(False)
        self.status_panel.set_status("已停止")
        self._is_searching = False
        self._is_downloading = False

    @Slot(list)
    def _on_search_done(self, papers: list):
        """搜索完成"""
        self._is_searching = False
        self.search_panel.set_searching(False)
        self.results_table.populate(papers)
        self.status_panel.reset_progress()
        self.statusBar().showMessage(f"搜索完成: {len(papers)} 篇论文", 5000)

    def _on_fetch_details(self, papers: list):
        """获取论文详情"""
        if not self._worker or not self._worker.is_browser_ready():
            QMessageBox.warning(self, "提示", "请先启动浏览器")
            return

        self.status_panel.reset_progress()
        self._worker.post_command(WorkerCommand(
            CommandType.FETCH_DETAILS, {"papers": papers}
        ))

    @Slot(list)
    def _on_details_done(self, papers: list):
        """详情获取完成"""
        # 更新表格中的论文数据
        all_papers = self.results_table.get_all_papers()
        for updated_paper in papers:
            for i, existing in enumerate(all_papers):
                if existing.title == updated_paper.title:
                    all_papers[i] = updated_paper
                    self.results_table.update_row(i, updated_paper)
                    break
        self.status_panel.reset_progress()
        self.statusBar().showMessage("详情获取完成", 5000)

    def _on_download_pdfs(self, papers: list):
        """下载PDF"""
        if not self._worker or not self._worker.is_browser_ready():
            QMessageBox.warning(self, "提示", "请先启动浏览器")
            return

        output_dir = self.export_panel.get_output_dir()
        if not output_dir:
            output_dir = QFileDialog.getExistingDirectory(self, "选择下载目录")
            if not output_dir:
                return

        self._is_downloading = True
        self.status_panel.reset_progress()
        self._worker.post_command(WorkerCommand(
            CommandType.DOWNLOAD_PDFS,
            {"papers": papers, "output_dir": output_dir}
        ))

    @Slot(str, bool, str)
    def _on_download_done(self, title: str, success: bool, message: str):
        """单个下载完成"""
        if success:
            self.results_table.mark_downloaded(title)

    @Slot(dict)
    def _on_download_batch_done(self, stats: dict):
        """批量下载完成"""
        self._is_downloading = False
        self.status_panel.reset_progress()
        total_ok = stats.get("pdf", 0) + stats.get("caj", 0)
        total = total_ok + stats.get("failed", 0) + stats.get("no_pdf_link", 0)
        self.statusBar().showMessage(
            f"下载完成: {total_ok}/{total} 成功 "
            f"(PDF: {stats.get('pdf', 0)}, CAJ: {stats.get('caj', 0)}, "
            f"失败: {stats.get('failed', 0)})", 10000
        )

    def _on_export(self, params: dict):
        """导出"""
        selected = self.results_table.get_selected_papers()
        if not selected:
            # 如果没有选中，导出全部
            selected = self.results_table.get_all_papers()
            if not selected:
                QMessageBox.warning(self, "提示", "没有可导出的论文")
                return

        params["papers"] = selected
        output_dir = params.get("output_dir", "")

        # 导出元数据
        options = params.get("options", {})
        if options.get("titles") or options.get("citations") or options.get("abstracts"):
            if self._worker:
                self._worker.post_command(WorkerCommand(CommandType.EXPORT, params))

        # 下载PDF (如果有勾选)
        if options.get("pdfs"):
            self._on_download_pdfs(selected)

    @Slot(str)
    def _on_export_done(self, filepath: str):
        """导出完成"""
        self.statusBar().showMessage(f"导出完成: {filepath}", 5000)

    @Slot()
    def _on_captcha(self):
        """验证码提示"""
        self.statusBar().showMessage(
            "检测到验证码，请在弹出的浏览器窗口中完成验证...", 30000
        )
        self.status_panel.append_log(">>> 请在浏览器窗口中完成验证码验证 <<<")

    @Slot(bool)
    def _on_browser_ready(self, ready: bool):
        """浏览器就绪"""
        if ready:
            self.browser_status.setText("浏览器: 已连接")
            self.browser_status.setStyleSheet("color: #2da44e; font-weight: bold;")
            self.action_launch.setEnabled(False)
            self.action_close.setEnabled(True)
            self.action_refresh_session.setEnabled(True)
            self.statusBar().showMessage("浏览器已就绪")
        else:
            self.browser_status.setText("浏览器: 未连接")
            self.browser_status.setStyleSheet("color: #cf222e;")
            self.action_launch.setEnabled(True)
            self.action_close.setEnabled(False)
            self.action_refresh_session.setEnabled(False)
            self.statusBar().showMessage("浏览器未连接")

    @Slot(str)
    def _on_session_status(self, status: str):
        """会话状态更新"""
        self.status_panel.append_log(f"会话: {status}")

    def _refresh_session(self):
        """手动刷新会话"""
        if self._worker:
            self.status_panel.append_log("手动刷新会话...")
            # 通过搜索一个空关键词来触发session refresh
            # 实际上我们可以添加一个专门的refresh命令

    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self, "关于",
            "CNKI 论文检索助手 v1.0\n\n"
            "功能:\n"
            "  - 知网论文搜索 (主题/篇名/关键词/摘要等)\n"
            "  - 批量获取论文详情 (摘要/关键词/DOI等)\n"
            "  - GB/T 7714-2025 格式引文生成\n"
            "  - 批量下载PDF原文\n"
            "  - 导出为 TXT/XLSX/DOCX 格式\n\n"
            "基于 Playwright 浏览器自动化技术"
        )

    def closeEvent(self, event):
        """窗口关闭时清理"""
        if self._worker:
            self._worker.request_stop()
        if self._worker_thread and self._worker_thread.isRunning():
            self._worker_thread.quit()
            self._worker_thread.wait(5000)
        event.accept()
