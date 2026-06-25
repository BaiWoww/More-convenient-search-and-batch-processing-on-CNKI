"""
CNKI Desktop - 配置模块
统一的CNKI检索与下载配置
"""

# ============================================================
# CNKI URLs
# ============================================================
CNKI_HOME_URL = "https://www.cnki.net/"
CNKI_BASE_URL = "https://kns.cnki.net/"
CNKI_SEARCH_URL = "https://kns.cnki.net/kns8s/defaultresult/index"
CNKI_SEARCH_API = "https://kns.cnki.net/kns8s/brief/grid"
CNKI_BAR_HOME = "https://bar.cnki.net/"

# ============================================================
# 数据库 ClassID 映射
# ============================================================
DATABASE_CLASSIDS = {
    "学术期刊": "YSTT4HG0",
    "硕士论文": "LSTPFY1C",
    "博士论文": "LSTPY0F2",
    "会议论文": "JUP3MUPD",
    "报纸": "CCND",
    "年鉴": "CYFD",
    "专利": "SCOD",
    "标准": "CISD",
}

DEFAULT_CLASSID = "YSTT4HG0"

# 数据库名称列表 (按常用顺序)
DATABASE_NAMES = list(DATABASE_CLASSIDS.keys())

# ============================================================
# 搜索字段代码映射
# ============================================================
SEARCH_FIELDS = {
    "主题": "SU",
    "篇关摘": "TKA",
    "关键词": "KY",
    "篇名": "TI",
    "全文": "FT",
    "作者": "AU",
    "第一作者": "FI",
    "通讯作者": "RP",
    "作者单位": "AF",
    "基金": "FU",
    "摘要": "AB",
    "小标题": "CO",
    "参考文献": "RF",
    "分类号": "CLC",
    "文献来源": "LY",
    "DOI": "DOI",
}

# 搜索字段名称列表
SEARCH_FIELD_NAMES = list(SEARCH_FIELDS.keys())

# ============================================================
# CSS 选择器 - 详情页解析
# ============================================================
DETAIL_SELECTORS = {
    "title": ["#chTitle", ".title", "h1", "#mainTitle"],
    "authors": "#chAuthor a, .author a, .authorinfo a",
    "institution": "#chInstitution, .institution, .orgn a",
    "abstract_cn": "#ChDivSummary",
    "abstract_en": "#ChDivSummaryEn, .abstract-text-en",
    "abstract_fallback": ".abstract-text, .abstract, [id*='abstract'], [class*='abstract']",
    "keywords": "#catalog_KEYWORD a, .kw-box a, .keywords a",
    "doi": "#catalog_DOI a, .doi a, a[href*='doi.org']",
    "journal": "#catalog_JOURNAL a, .journal-name a",
    "year": "#catalog_YEAR, .year",
    "fund": "#catalog_FUND a, .fund a",
    "cited_count": "#catalog_CITATION a, .citation-num",
    "download_count": "#catalog_DOWNLOAD a, .download-num",
    "references": "#catalog_RefText li, .reference-list li",
    "citations": "#catalog_CITING li, .citing-list li",
    "pdf_download": "#pdfDown",
    "pdf_download_alt": "a[href*='pdf']",
    # 卷/期/页码选择器 (用于GB/T 7714-2025引文)
    "volume": "#catalog_VOLUME, .volume",
    "issue": "#catalog_ISSUE, .issue, .period",
    "pages": "#catalog_PAGE, .page",
}

# 机构名称关键词 (用于区分作者和机构)
INSTITUTION_KEYWORDS = [
    "大学", "学院", "研究所", "研究中心", "科学院", "研究院",
    "检测中心", "执法", "技术推广", "实验室",
]

# ============================================================
# 浏览器与反检测配置
# ============================================================
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--disable-dev-shm-usage",
]

STEALTH_JS = """() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en-US', 'en'] });
    window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){}, app: {} };
    const origQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (params) =>
        params.name === 'notifications'
            ? Promise.resolve({ state: Notification.permission })
            : origQuery(params);
    const getParam = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(p) {
        if (p === 37445) return 'Intel Inc.';
        if (p === 37446) return 'Intel Iris OpenGL Engine';
        return getParam.apply(this, arguments);
    };
}"""

# ============================================================
# 时间控制
# ============================================================
QUERY_DELAY = 1.2          # 搜索间隔 (秒)
DETAIL_DELAY = 2.5         # 详情页间隔 (秒)
SEARCH_DELAY = 2.0         # 下载搜索间隔 (秒)
NAVIGATE_DELAY = 3         # 页面导航后等待 (秒)
DOWNLOAD_TIMEOUT = 60000   # 下载超时 (毫秒)
PAGE_LOAD_TIMEOUT = 30000  # 页面加载超时 (毫秒)
DOWNLOADS_PER_SESSION = 10 # 每次session下载次数上限
SESSION_REFRESH_DELAY = 3.0  # session刷新后等待 (秒)
MAX_RETRIES = 2            # 每篇论文最大重试次数

EMPTY_PAUSE = 30           # 连续空结果后暂停 (秒)
EMPTY_THRESHOLD = 5        # 连续空结果阈值

# ============================================================
# 文件格式检测
# ============================================================
PLACEHOLDER_MD5 = "15a81035d44dcc83d72aa9445f237b42"

CAJ_HEADERS = [
    b'\xc8\x00\x00\x00',  # CAJ type 1
    b'HN\x00\x00',         # CAJ type 2
    b'KDH ',                # KDH format
    b'\xc8\xa0\xc8\xa0',  # CAJ type 3
]

def detect_format(data: bytes) -> str:
    """通过文件头字节检测文件格式。
    返回: 'pdf', 'caj', 'html_error', 或 'unknown'
    """
    if data[:5] == b'%PDF-':
        return 'pdf'
    for header in CAJ_HEADERS:
        if data[:len(header)] == header:
            return 'caj'
    if data[:9].lower().startswith(b'<!doctype') or data[:6].lower().startswith(b'<html'):
        return 'html_error'
    return 'unknown'

# ============================================================
# 浏览器配置文件路径
# ============================================================
import os
APP_DATA_DIR = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")),
    "cnki-desktop"
)
BROWSER_PROFILE_DIR = os.path.join(APP_DATA_DIR, "browser-profile")
