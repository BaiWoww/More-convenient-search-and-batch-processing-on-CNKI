"""
CNKI Desktop - 下载模块
PDF下载、会话管理、文件格式检测
"""
import os
import re
import time

from core.config import (
    CNKI_SEARCH_URL, CNKI_BAR_HOME,
    DOWNLOAD_TIMEOUT, SEARCH_DELAY, DOWNLOADS_PER_SESSION,
    SESSION_REFRESH_DELAY, NAVIGATE_DELAY, MAX_RETRIES,
    detect_format,
)
from core.api import ajax_search, parse_search_results, match_paper


def safe_filename(title, max_len=60):
    """从论文标题创建文件系统安全文件名"""
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', title)
    clean = re.sub(r'\s+', ' ', clean).strip()
    if len(clean) > max_len:
        clean = clean[:max_len].rsplit(' ', 1)[0]
    return clean or "untitled"


def get_pdf_url_from_detail(page, detail_url, title=""):
    """导航到详情页并提取 #pdfDown href (PDF下载链接)。

    CNKI详情页的 #pdfDown 元素包含 bar.cnki.net URL，
    返回PDF格式 (搜索结果中的bar URL返回CAJ)。

    Args:
        page: Playwright page对象
        detail_url: 论文详情页URL
        title: 论文标题 (用于日志)

    Returns: PDF下载URL字符串或None
    """
    from playwright.sync_api import TimeoutError as PwTimeout
    try:
        page.goto(detail_url, wait_until="domcontentloaded", timeout=30000)
    except PwTimeout:
        return None, "timeout"
    except Exception as e:
        return None, f"nav_error: {e}"

    time.sleep(NAVIGATE_DELAY)

    # 主选: 直接查询 #pdfDown
    try:
        pdf_el = page.query_selector('#pdfDown')
        if pdf_el:
            href = pdf_el.get_attribute('href') or ''
            if href and 'bar.cnki.net' in href:
                return href, "ok"
    except Exception:
        pass

    # 备选: JS查询
    try:
        fallback = page.evaluate("""() => {
            let el = document.getElementById('pdfDown');
            if (el && el.href) return el.href;
            el = document.querySelector('a[name="pdfDown"]');
            if (el && el.href) return el.href;
            const links = document.querySelectorAll('a[href*="bar.cnki.net"]');
            for (const a of links) {
                if ((a.innerText || '').toUpperCase().includes('PDF')) {
                    return a.href;
                }
            }
            return null;
        }""")
        if fallback:
            return fallback, "ok"
    except Exception:
        pass

    return None, "no_pdf_link"


def browser_download(page, bar_url, filepath):
    """通过浏览器下载机制下载文件。

    创建临时 <a> 元素，点击并捕获下载。

    Returns: (success: bool, format: str, size: int)
    """
    from playwright.sync_api import TimeoutError as PwTimeout

    try:
        with page.expect_download(timeout=DOWNLOAD_TIMEOUT) as dl_info:
            safe_url = bar_url.replace("'", "\\'")
            page.evaluate(f"""() => {{
                const a = document.createElement('a');
                a.href = '{safe_url}';
                a.download = 'paper';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            }}""")
        download = dl_info.value
    except PwTimeout:
        return False, "timeout", 0
    except Exception as e:
        return False, "error", 0

    # 先保存到临时文件
    tmp_path = filepath + ".tmp"
    try:
        download.save_as(tmp_path)
    except Exception as e:
        return False, "save_error", 0

    # 读取文件头检测格式
    try:
        with open(tmp_path, 'rb') as f:
            header = f.read(512)
    except Exception:
        _try_remove(tmp_path)
        return False, "read_error", 0

    fmt = detect_format(header)
    file_size = os.path.getsize(tmp_path)

    if fmt == 'html_error':
        _try_remove(tmp_path)
        return False, "session_expired", file_size

    if fmt == 'unknown' and file_size < 5000:
        _try_remove(tmp_path)
        return False, "too_small", file_size

    # 确定最终扩展名
    ext = '.pdf' if fmt == 'pdf' else '.caj' if fmt == 'caj' else '.pdf'
    final_path = filepath + ext

    try:
        if os.path.exists(final_path):
            os.remove(final_path)
        os.rename(tmp_path, final_path)
    except Exception:
        _try_remove(tmp_path)
        return False, "rename_error", file_size

    return True, fmt, file_size


def refresh_session(page, ctx):
    """刷新 bar.cnki.net 会话。

    bar.cnki.net 重定向到 www.cnki.net 但设置新鲜的 JSESSIONID + SID_bar cookies。
    """
    from playwright.sync_api import TimeoutError as PwTimeout
    try:
        page.goto(CNKI_BAR_HOME, wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)
    except PwTimeout:
        pass

    try:
        page.goto(CNKI_SEARCH_URL, wait_until="domcontentloaded", timeout=20000)
        time.sleep(SESSION_REFRESH_DELAY)
    except PwTimeout:
        pass

    bar_cookies = [c for c in ctx.cookies() if 'bar.cnki.net' in c.get('domain', '')]
    return len(bar_cookies) > 0


def _try_remove(path):
    """安全删除临时文件"""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
