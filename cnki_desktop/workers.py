"""
CNKI Desktop - Worker 线程模块
在独立线程中管理 Playwright 浏览器操作，通过 Qt 信号与 GUI 通信
"""
import enum
import os
import queue
import time
import traceback
from dataclasses import dataclass
from typing import Any, Optional

from PySide6.QtCore import QObject, QThread, Signal, QMutex

from core.config import (
    BROWSER_PROFILE_DIR, CNKI_HOME_URL, CNKI_SEARCH_URL, CNKI_BAR_HOME,
    BROWSER_ARGS, STEALTH_JS, USER_AGENT,
    QUERY_DELAY, DETAIL_DELAY, SEARCH_DELAY, NAVIGATE_DELAY,
    DOWNLOADS_PER_SESSION, SESSION_REFRESH_DELAY, MAX_RETRIES,
)
from core.api import (
    Paper, ajax_search, parse_search_results,
    parse_detail, fetch_via_browser, normalize_title, match_paper,
)
from core.download import (
    safe_filename, get_pdf_url_from_detail,
    browser_download, refresh_session,
)
from core.exporter import (
    export_titles_txt, export_titles_xlsx,
    export_citations_txt, export_citations_docx,
    export_abstracts_txt, export_abstracts_docx,
)


class CommandType(enum.Enum):
    INIT_BROWSER = "init_browser"
    SEARCH = "search"
    FETCH_DETAILS = "fetch_details"
    DOWNLOAD_PDFS = "download_pdfs"
    EXPORT = "export"
    STOP = "stop"
    CLOSE_BROWSER = "close_browser"


@dataclass
class WorkerCommand:
    command: CommandType
    payload: Any = None


class BrowserWorker(QObject):
    """在独立线程中运行的 Playwright 浏览器工作器。

    信号:
        log(str): 日志消息
        progress(int, int): 进度 (当前, 总数)
        search_done(list): 搜索完成，返回 Paper 列表
        details_done(list): 详情获取完成，返回更新后的 Paper 列表
        download_done(str, bool, str): 单个下载完成 (标题, 成功, 消息)
        download_batch_done(dict): 批量下载完成 (统计信息)
        export_done(str): 导出完成 (文件路径)
        error(str): 错误消息
        captcha_required(): 需要验证码
        browser_ready(bool): 浏览器就绪状态
        session_status(str): 会话状态消息
    """

    log = Signal(str)
    progress = Signal(int, int)
    search_done = Signal(list)
    details_done = Signal(list)
    download_done = Signal(str, bool, str)
    download_batch_done = Signal(dict)
    export_done = Signal(str)
    error = Signal(str)
    captcha_required = Signal()
    browser_ready = Signal(bool)
    session_status = Signal(str)

    def __init__(self):
        super().__init__()
        self._queue = queue.Queue()
        self._stop_event = False
        self._pw = None
        self._browser = None
        self._ctx = None
        self._page = None
        self._browser_ready = False
        self._mutex = QMutex()

    def post_command(self, cmd: WorkerCommand):
        """线程安全地发送命令到工作器"""
        self._queue.put(cmd)

    def request_stop(self):
        """请求停止工作器"""
        self._stop_event = True
        self._queue.put(WorkerCommand(CommandType.STOP))

    def is_browser_ready(self):
        return self._browser_ready

    def _init_browser(self):
        """初始化 Playwright 浏览器"""
        try:
            from playwright.sync_api import sync_playwright
            self.log.emit("正在启动浏览器...")

            self._pw = sync_playwright().start()

            # 使用持久化上下文，保留登录状态
            os.makedirs(BROWSER_PROFILE_DIR, exist_ok=True)

            self._ctx = self._pw.chromium.launch_persistent_context(
                BROWSER_PROFILE_DIR,
                headless=False,
                channel="msedge",
                args=BROWSER_ARGS,
                ignore_default_args=["--enable-automation"],
                accept_downloads=True,
                viewport={"width": 1280, "height": 800},
                locale="zh-CN",
                timezone_id="Asia/Shanghai",
                user_agent=USER_AGENT,
            )
            self._ctx.add_init_script(STEALTH_JS)

            if self._ctx.pages:
                self._page = self._ctx.pages[0]
            else:
                self._page = self._ctx.new_page()

            # 导航到 CNKI 建立 session
            self.log.emit("正在连接 CNKI...")
            try:
                self._page.goto(CNKI_HOME_URL, wait_until="domcontentloaded", timeout=20000)
                time.sleep(2)
            except Exception:
                pass

            try:
                self._page.goto(CNKI_SEARCH_URL, wait_until="domcontentloaded", timeout=20000)
                time.sleep(2)
            except Exception:
                pass

            self._browser_ready = True
            self.browser_ready.emit(True)
            self.log.emit("浏览器已就绪")
            self.session_status.emit("已连接")

        except Exception as e:
            self._browser_ready = False
            self.browser_ready.emit(False)
            self.error.emit(f"浏览器初始化失败: {e}")

    def _close_browser(self):
        """关闭浏览器"""
        try:
            if self._ctx:
                self._ctx.close()
            if self._pw:
                self._pw.stop()
            self._browser_ready = False
            self.browser_ready.emit(False)
            self.log.emit("浏览器已关闭")
        except Exception as e:
            pass

    def _check_captcha(self):
        """检查当前页面是否触发了验证码。
        使用精确匹配避免误报：
        - 只检查URL中的CNKI验证码路径
        - 只检查页面标题（不检查完整HTML内容中的JS代码）
        - 检查页面上是否显示验证码UI元素
        """
        try:
            url = self._page.url

            # 1. URL 检测: CNKI 验证码页面的 URL 特征
            if "wappass" in url:
                return True
            # 只匹配验证码相关的 verify 路径，不匹配其他包含 verify 的 URL
            if "/Verify" in url or "/verify?" in url or "verify.aspx" in url:
                return True

            # 2. 页面标题检测: 验证码页面的标题特征
            title = self._page.title() or ""
            if "安全验证" in title or "验证" == title.strip():
                return True

            # 3. 可见内容检测: 只检查 body 可见文本，忽略 JS/CSS
            try:
                body_text = self._page.evaluate("""() => {
                    const el = document.querySelector('.verify-wrap, .verify-box, #verify-img, .captcha-wrap');
                    if (el) return 'CAPTCHA_FOUND';
                    const title = document.title || '';
                    if (title.includes('安全验证')) return 'CAPTCHA_FOUND';
                    // 检查是否有明显的验证码遮罩层
                    const overlay = document.querySelector('.verify-mask, .dialog-mask');
                    if (overlay && overlay.offsetParent !== null) return 'CAPTCHA_FOUND';
                    return '';
                }""")
                return body_text == "CAPTCHA_FOUND"
            except Exception:
                return False

        except Exception:
            return False

    def _wait_captcha_resolution(self, timeout=300):
        """等待验证码被解决"""
        start = time.time()
        while time.time() - start < timeout:
            if self._stop_event:
                return False
            if not self._check_captcha():
                return True
            time.sleep(3)
        return False

    def _do_search(self, params: dict):
        """执行搜索"""
        keyword = params.get("keyword", "")
        field = params.get("field", "SU")
        classid = params.get("classid", "YSTT4HG0")
        max_pages = params.get("max_pages", 3)

        if not self._browser_ready:
            self.error.emit("浏览器未就绪，请先启动浏览器")
            return

        self.log.emit(f"开始搜索: {keyword} (字段: {field}, 数据库: {classid})")

        all_papers = []
        seen_titles = set()

        for page_num in range(1, max_pages + 1):
            if self._stop_event:
                self.log.emit("搜索已取消")
                break

            self.progress.emit(page_num, max_pages)
            self.log.emit(f"正在搜索第 {page_num}/{max_pages} 页...")

            papers_data, err = ajax_search(
                self._page, keyword, field=field,
                classid=classid, page_num=page_num, page_size=20
            )

            if err == "captcha":
                self.log.emit("检测到验证码，请在浏览器窗口中完成验证...")
                self.captcha_required.emit()
                if not self._wait_captcha_resolution():
                    self.error.emit("验证码处理超时或已取消")
                    break
                # 验证通过后重试当前页
                papers_data, err = ajax_search(
                    self._page, keyword, field=field,
                    classid=classid, page_num=page_num, page_size=20
                )
                if err:
                    self.error.emit(f"搜索出错: {err}")
                    break

            if not papers_data:
                self.log.emit(f"第 {page_num} 页没有更多结果")
                break

            new_count = 0
            for pd in papers_data:
                title = pd["title"].strip()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    paper = Paper.from_search_result(pd, classid)
                    paper.search_query = keyword
                    paper.search_field = field
                    paper.search_classid = classid
                    all_papers.append(paper)
                    new_count += 1

            self.log.emit(f"第 {page_num} 页: 获取 {len(papers_data)} 条，新增 {new_count} 条")

            if not papers_data:
                break

            time.sleep(QUERY_DELAY)

        self.search_done.emit(all_papers)
        self.log.emit(f"搜索完成: 共找到 {len(all_papers)} 篇论文")

    def _do_fetch_details(self, params: dict):
        """获取论文详情"""
        papers = params.get("papers", [])
        total = len(papers)

        if not self._browser_ready:
            self.error.emit("浏览器未就绪，请先启动浏览器")
            return

        self.log.emit(f"开始获取 {total} 篇论文的详细信息...")
        updated = []

        for i, paper in enumerate(papers):
            if self._stop_event:
                self.log.emit("获取详情已取消")
                break

            self.progress.emit(i + 1, total)
            self.log.emit(f"[{i+1}/{total}] 获取: {paper.title[:50]}...")

            url = paper.url
            if not url:
                updated.append(paper)
                continue

            # 确保是完整 URL
            if not url.startswith("http"):
                url = "https://kns.cnki.net" + url

            try:
                # 检查验证码
                if self._check_captcha():
                    self.log.emit("检测到验证码，请在浏览器窗口中完成验证...")
                    self.captcha_required.emit()
                    if not self._wait_captcha_resolution():
                        self.error.emit("验证码处理超时")
                        updated.append(paper)
                        continue

                self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(DETAIL_DELAY)

                html = self._page.content()
                if html and len(html) > 500:
                    paper = parse_detail(html, paper)
                    self.log.emit(f"  -> 详情获取成功")
                else:
                    self.log.emit(f"  -> 详情页内容为空")

            except Exception as e:
                self.log.emit(f"  -> 获取失败: {e}")

            updated.append(paper)

        self.details_done.emit(updated)
        self.log.emit(f"详情获取完成: {len(updated)}/{total} 篇")

    def _do_download_pdfs(self, params: dict):
        """批量下载 PDF"""
        papers = params.get("papers", [])
        output_dir = params.get("output_dir", "")
        total = len(papers)

        if not self._browser_ready:
            self.error.emit("浏览器未就绪，请先启动浏览器")
            return

        if not output_dir:
            self.error.emit("未指定输出目录")
            return

        os.makedirs(output_dir, exist_ok=True)
        self.log.emit(f"开始下载 {total} 篇论文 PDF...")

        stats = {"pdf": 0, "caj": 0, "failed": 0, "no_pdf_link": 0, "session_expired": 0}
        session_count = 0

        for i, paper in enumerate(papers):
            if self._stop_event:
                self.log.emit("下载已取消")
                break

            self.progress.emit(i + 1, total)

            title = paper.title.strip()
            fname = safe_filename(title)
            filepath = os.path.join(output_dir, fname)

            # 检查是否已下载
            pdf_path = filepath + ".pdf"
            if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 5000:
                self.log.emit(f"[{i+1}/{total}] 已存在: {fname}")
                self.download_done.emit(title, True, "已存在")
                stats["pdf"] += 1
                continue

            # session 刷新
            if session_count >= DOWNLOADS_PER_SESSION:
                self.log.emit("正在刷新会话...")
                refresh_session(self._page, self._ctx)
                session_count = 0

            # 获取 PDF URL
            url = paper.url
            if not url:
                self.log.emit(f"[{i+1}/{total}] 无详情页链接: {title[:40]}")
                self.download_done.emit(title, False, "无链接")
                stats["failed"] += 1
                continue

            if not url.startswith("http"):
                url = "https://kns.cnki.net" + url

            success = False
            for attempt in range(MAX_RETRIES + 1):
                if self._stop_event:
                    break

                # 检查验证码
                if self._check_captcha():
                    self.log.emit("检测到验证码，请在浏览器窗口中完成验证...")
                    self.captcha_required.emit()
                    if not self._wait_captcha_resolution():
                        break

                pdf_url, err = get_pdf_url_from_detail(self._page, url, title)

                if not pdf_url:
                    if attempt < MAX_RETRIES:
                        self.log.emit(f"  重试 ({attempt+2}/{MAX_RETRIES+1})...")
                        time.sleep(2)
                        try:
                            self._page.goto(CNKI_SEARCH_URL,
                                          wait_until="domcontentloaded", timeout=20000)
                            time.sleep(2)
                        except Exception:
                            pass
                    else:
                        stats["no_pdf_link"] += 1
                        self.download_done.emit(title, False, f"无PDF链接: {err}")
                    continue

                # 下载
                ok, fmt, size = browser_download(self._page, pdf_url, filepath)
                if ok:
                    size_kb = size / 1024
                    self.log.emit(f"[{i+1}/{total}] 下载成功: {fmt.upper()} ({size_kb:.0f} KB)")
                    self.download_done.emit(title, True, f"{fmt.upper()} {size_kb:.0f}KB")
                    stats[fmt] = stats.get(fmt, 0) + 1
                    session_count += 1
                    success = True
                    break
                elif fmt == "session_expired":
                    self.log.emit("  会话已过期，正在刷新...")
                    refresh_session(self._page, self._ctx)
                    session_count = 0
                    stats["session_expired"] += 1
                    time.sleep(SEARCH_DELAY)
                else:
                    self.download_done.emit(title, False, fmt)
                    stats["failed"] += 1
                    break

            if not success:
                stats["failed"] += 1
                self.download_done.emit(title, False, "下载失败")

            # 回到搜索页
            try:
                self._page.goto(CNKI_SEARCH_URL,
                              wait_until="domcontentloaded", timeout=20000)
                time.sleep(1)
            except Exception:
                pass

            time.sleep(SEARCH_DELAY)

        self.download_batch_done.emit(stats)
        total_ok = stats.get("pdf", 0) + stats.get("caj", 0)
        self.log.emit(f"下载完成: {total_ok}/{total} 成功")

    def _do_export(self, params: dict):
        """导出数据"""
        papers = params.get("papers", [])
        output_dir = params.get("output_dir", "")
        options = params.get("options", {})

        if not output_dir:
            self.error.emit("未指定输出目录")
            return

        os.makedirs(output_dir, exist_ok=True)
        exported_files = []

        # 导出标题
        if options.get("titles"):
            fmt = options.get("titles_format", "txt")
            if fmt == "xlsx":
                path = os.path.join(output_dir, "论文列表.xlsx")
                export_titles_xlsx(papers, path)
            else:
                path = os.path.join(output_dir, "论文列表.txt")
                export_titles_txt(papers, path)
            exported_files.append(path)
            self.log.emit(f"已导出标题: {path}")

        # 导出引文
        if options.get("citations"):
            fmt = options.get("citations_format", "txt")
            if fmt == "docx":
                path = os.path.join(output_dir, "参考文献_GB-T_7714.docx")
                export_citations_docx(papers, path)
            else:
                path = os.path.join(output_dir, "参考文献_GB-T_7714.txt")
                export_citations_txt(papers, path)
            exported_files.append(path)
            self.log.emit(f"已导出引文: {path}")

        # 导出摘要
        if options.get("abstracts"):
            fmt = options.get("abstracts_format", "txt")
            if fmt == "docx":
                path = os.path.join(output_dir, "论文摘要汇编.docx")
                export_abstracts_docx(papers, path)
            else:
                path = os.path.join(output_dir, "论文摘要汇编.txt")
                export_abstracts_txt(papers, path)
            exported_files.append(path)
            self.log.emit(f"已导出摘要: {path}")

        for f in exported_files:
            self.export_done.emit(f)

        self.log.emit(f"导出完成，共 {len(exported_files)} 个文件")

    def run(self):
        """工作器主循环 - 在 QThread 的 started 信号中调用。
        自动初始化浏览器，然后进入命令循环。
        """
        # 自动初始化浏览器
        self._init_browser()

        while not self._stop_event:
            try:
                cmd = self._queue.get(timeout=1)
            except queue.Empty:
                continue

            if cmd.command == CommandType.STOP:
                break

            try:
                if cmd.command == CommandType.INIT_BROWSER:
                    self._init_browser()
                elif cmd.command == CommandType.CLOSE_BROWSER:
                    self._close_browser()
                elif cmd.command == CommandType.SEARCH:
                    self._do_search(cmd.payload)
                elif cmd.command == CommandType.FETCH_DETAILS:
                    self._do_fetch_details(cmd.payload)
                elif cmd.command == CommandType.DOWNLOAD_PDFS:
                    self._do_download_pdfs(cmd.payload)
                elif cmd.command == CommandType.EXPORT:
                    self._do_export(cmd.payload)
            except Exception as e:
                tb = traceback.format_exc()
                self.error.emit(f"操作出错: {e}\n{tb}")

        # 清理
        if self._browser_ready:
            self._close_browser()
