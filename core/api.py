"""
CNKI Desktop - CNKI API 模块
搜索、解析搜索结果和详情页的核心功能
"""
import json
import re
import time
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import quote

from bs4 import BeautifulSoup

from core.config import (
    CNKI_SEARCH_API, CNKI_SEARCH_URL, CNKI_HOME_URL, CNKI_BASE_URL,
    DETAIL_SELECTORS, INSTITUTION_KEYWORDS,
    QUERY_DELAY, DETAIL_DELAY, PAGE_LOAD_TIMEOUT,
    EMPTY_PAUSE, EMPTY_THRESHOLD,
)


@dataclass
class Paper:
    """论文数据模型"""
    title: str = ""
    authors: List[str] = field(default_factory=list)
    institutions: List[str] = field(default_factory=list)
    journal: str = ""
    date: str = ""
    year: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    abstract: str = ""
    abstract_en: str = ""
    keywords: List[str] = field(default_factory=list)
    doi: str = ""
    fund: List[str] = field(default_factory=list)
    url: str = ""
    pdf_url: str = ""
    dbname: str = ""
    filename: str = ""
    cited_count: str = ""
    download_count: str = ""
    reference_count: int = 0
    references_preview: List[str] = field(default_factory=list)
    citation_count: int = 0
    relevance_score: int = 0
    search_query: str = ""
    search_field: str = ""
    search_classid: str = ""
    doc_type: str = ""  # J/D/C/N/P/S
    # 引用信息
    citation_text: str = ""  # GB/T 7714-2025 格式引文
    citation_fetched: bool = False
    # GUI状态
    selected: bool = False
    detail_fetched: bool = False
    pdf_downloaded: bool = False
    local_pdf_path: str = ""
    status: str = ""

    @staticmethod
    def from_search_result(d: dict, classid: str = "") -> "Paper":
        """从搜索结果字典创建Paper对象"""
        p = Paper(
            title=d.get("title", ""),
            authors=d.get("authors", []),
            journal=d.get("journal", ""),
            date=d.get("date", ""),
            cited_count=d.get("cited", ""),
            download_count=d.get("downloads", ""),
            url=d.get("url", ""),
            dbname=d.get("dbname", ""),
            filename=d.get("filename", ""),
        )
        # 从classid推断文档类型
        type_map = {
            "YSTT4HG0": "J", "LSTPFY1C": "D", "LSTPY0F2": "D",
            "JUP3MUPD": "C", "CCND": "N", "CYFD": "A",
            "SCOD": "P", "CISD": "S",
        }
        p.doc_type = type_map.get(classid, "")
        # 提取年份
        if p.date:
            match = re.search(r'(\d{4})', p.date)
            if match:
                p.year = match.group(1)
        return p

    @staticmethod
    def from_dict(d: dict) -> "Paper":
        """从字典创建Paper对象"""
        p = Paper()
        for k, v in d.items():
            if hasattr(p, k):
                setattr(p, k, v)
        return p


FIELD_KEY_MAP = {
    "SU": "Subject",
    "TKA": "TitleKeywordAbstract",
    "KY": "Keyword",
    "TI": "Title",
    "FT": "FullText",
    "AU": "Author",
    "FI": "FirstAuthor",
    "RP": "CorrespondingAuthor",
    "AF": "Organization",
    "FU": "Fund",
    "AB": "Abstract",
    "CO": "SubTitle",
    "RF": "Reference",
    "CLC": "CLC",
    "LY": "Journal",
    "DOI": "DOI",
}

FIELD_OPERATOR_MAP = {
    "SU": "TOPRANK",
    "TKA": "%",
    "KY": "=",
    "TI": "%",
    "FT": "%",
    "AU": "=",
    "FI": "=",
    "RP": "%",
    "AF": "%",
    "FU": "%",
    "AB": "%",
    "CO": "%",
    "RF": "%",
    "CLC": "=",
    "LY": "%",
    "DOI": "=",
}


def ajax_search(page, keyword, field="SU", classid=None, page_num=1, page_size=20):
    """执行CNKI AJAX搜索，返回论文字典列表。

    Args:
        page: Playwright Page对象 (需要有活跃CNKI session cookies)
        keyword: 搜索关键词
        field: 搜索字段代码 (SU=主题, TI=篇名, KY=关键词等)
        classid: 数据库ClassID (默认: YSTT4HG0 = 学术期刊)
        page_num: 页码 (从1开始)
        page_size: 每页结果数 (最大20)

    Returns:
        论文字典列表
    """
    classid = classid or "YSTT4HG0"
    qnode_key = FIELD_KEY_MAP.get(field, "Subject")
    operator = FIELD_OPERATOR_MAP.get(field, "TOPRANK")

    query_json = json.dumps({
        "Platform": "", "Resource": "",
        "Classid": classid,
        "Products": "",
        "QNode": {"QGroup": [{"Key": qnode_key, "Title": "", "Logic": 0,
            "Items": [{"Field": field, "Value": keyword,
                        "Operator": operator,
                        "Logic": 0}],
            "ChildItems": []}]},
        "ExScope": 1, "SearchType": 7, "Rlang": "CHINESE", "KuaKuCode": "",
    }, ensure_ascii=False)

    post_data = (
        "boolSearch=false"
        + "&QueryJson=" + quote(query_json)
        + "&pageNum=" + str(page_num)
        + "&pageSize=" + str(page_size)
        + "&sortField=PT&sortType=desc"
        + "&dstyle=listmode&aside=&searchFrom="
    )

    fetch_js = """
    async ([url, body]) => {
        try {
            const resp = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": "https://kns.cnki.net/kns8s/defaultresult/index",
                },
                body: body, credentials: "include",
            });
            return { status: resp.status, body: await resp.text() };
        } catch(e) {
            return { status: -1, body: "ERROR: " + e.message };
        }
    }
    """

    try:
        result = page.evaluate(fetch_js, [CNKI_SEARCH_API, post_data])
    except Exception as e:
        return [], f"Fetch error: {e}"

    html = result.get("body", "")

    # 检测验证码
    if "verify" in html.lower() or "安全验证" in html:
        return [], "captcha"

    papers = parse_search_results(html)
    return papers, None


def parse_search_results(html):
    """解析CNKI搜索结果HTML为论文字典列表。
    
    根据 cnki.md 提供的 HTML 结构优化选择器。

    Returns: list of {title, authors, journal, date, cited, downloads, url, dbname, filename, bar_url}
    """
    soup = BeautifulSoup(html, "lxml")
    papers = []

    for row in soup.find_all("tr"):
        # 检查是否有 cbItem checkbox（确认是有效结果行）
        checkbox = row.select_one("input.cbItem")
        if not checkbox:
            continue

        # 标题：td.name a.fz14
        title_elem = row.select_one("td.name a.fz14") or row.select_one("a.fz14")
        if not title_elem:
            continue
        title = title_elem.get_text(strip=True)
        href = title_elem.get("href", "")

        # 作者：td.author a.KnowledgeNetLink 或 td.author a
        authors = [a.get_text(strip=True) for a in row.select("td.author a.KnowledgeNetLink")
                   if a.get_text(strip=True)]
        if not authors:
            authors = [a.get_text(strip=True) for a in row.select("td.author a")
                       if a.get_text(strip=True)]

        # 来源：td.source
        source_elem = row.select_one("td.source a") or row.select_one("td.source")
        journal = source_elem.get_text(strip=True) if source_elem else ""

        # 日期：td.date
        date_elem = row.select_one("td.date")
        date = date_elem.get_text(strip=True) if date_elem else ""

        # 引用数：td.quote
        quote_elem = row.select_one("td.quote a") or row.select_one("td.quote")
        cited = quote_elem.get_text(strip=True) if quote_elem else ""

        # 下载数：td.download
        download_elem = row.select_one("td.download a") or row.select_one("td.download")
        downloads = download_elem.get_text(strip=True) if download_elem else ""

        # bar.cnki.net download URL
        dl_link = row.select_one("a.downloadlink")
        bar_url = dl_link.get("href", "") if dl_link else ""

        # DB metadata
        collect = row.select_one("a.icon-collect") or row.select_one("[data-dbname]")
        dbname = collect.get("data-dbname", "") if collect else ""
        filename = collect.get("data-filename", "") if collect else ""

        papers.append({
            "title": title, "authors": authors, "journal": journal,
            "date": date, "cited": cited, "downloads": downloads,
            "url": href, "dbname": dbname, "filename": filename,
            "bar_url": bar_url,
        })
    return papers


def fetch_via_browser(page, url):
    """通过浏览器fetch API获取URL内容 (保留cookies)"""
    try:
        return page.evaluate("""
            async (url) => {
                try { const r = await fetch(url, {credentials:"include"}); return await r.text(); }
                catch(e) { return ""; }
            }
        """, url)
    except Exception:
        return ""


def parse_detail(html, base_paper):
    """解析CNKI详情页HTML，合并到基础论文数据中。

    提取: 标题, 作者, 机构, 摘要, 关键词, DOI, 基金, 参考文献, 引用数, PDF URL,
          卷/期/页码 (用于引文生成)

    Args:
        html: 详情页完整HTML
        base_paper: Paper对象或字典

    Returns:
        更新后的Paper对象
    """
    if isinstance(base_paper, dict):
        paper = Paper.from_dict(base_paper)
    else:
        paper = base_paper

    soup = BeautifulSoup(html, "lxml")
    S = DETAIL_SELECTORS

    # 标题
    for sel in S["title"]:
        t = soup.select_one(sel)
        if t:
            txt = t.get_text(strip=True)
            if txt and len(txt) > 5 and "使用帮助" not in txt and "help" not in txt.lower():
                paper.title = txt
                break

    # 作者 & 机构
    author_elems = soup.select(S["authors"])
    all_texts = [a.get_text(strip=True) for a in author_elems if a.get_text(strip=True)]
    authors_clean, institutions = [], []
    for txt in all_texts:
        if any(kw in txt for kw in INSTITUTION_KEYWORDS):
            institutions.append(txt)
        else:
            clean = re.sub(r"[\d,，\s]+$", "", txt)
            if clean:
                authors_clean.append(clean)
    if authors_clean:
        paper.authors = authors_clean
    paper.institutions = institutions

    # 摘要 (中文)
    paper.abstract = ""
    for sel in [S["abstract_cn"], S["abstract_fallback"]]:
        if isinstance(sel, list):
            for s in sel:
                elem = soup.select_one(s)
                if elem and len(elem.get_text(strip=True)) > 30:
                    text = re.sub(r"^(摘\s*要|Abstract)[:：\s]*", "", elem.get_text(strip=True))
                    paper.abstract = text
                    break
            if paper.abstract:
                break
        else:
            elem = soup.select_one(sel)
            if elem and len(elem.get_text(strip=True)) > 30:
                text = re.sub(r"^(摘\s*要|Abstract)[:：\s]*", "", elem.get_text(strip=True))
                paper.abstract = text
                break

    # 摘要 (英文)
    ab_en = soup.select_one(S["abstract_en"])
    paper.abstract_en = ab_en.get_text(strip=True) if ab_en else ""

    # 关键词
    kws = soup.select(S["keywords"])
    paper.keywords = [k.get_text(strip=True).rstrip(";；") for k in kws
                      if k.get_text(strip=True)]

    # DOI
    doi_elem = soup.select_one(S["doi"])
    paper.doi = doi_elem.get_text(strip=True) if doi_elem else ""

    # 基金
    funds = soup.select(S["fund"])
    paper.fund = [f.get_text(strip=True) for f in funds if f.get_text(strip=True)]

    # 参考文献 & 引用
    refs = soup.select(S["references"])
    paper.reference_count = len(refs)
    paper.references_preview = [ref.get_text(strip=True) for ref in refs[:5]]

    cits = soup.select(S["citations"])
    paper.citation_count = len(cits)

    # 卷、期、页码 (用于引文)
    vol_el = soup.select_one(S["volume"])
    if vol_el:
        paper.volume = vol_el.get_text(strip=True)

    issue_el = soup.select_one(S["issue"])
    if issue_el:
        paper.issue = issue_el.get_text(strip=True)

    pages_el = soup.select_one(S["pages"])
    if pages_el:
        paper.pages = pages_el.get_text(strip=True)

    # 尝试从期刊信息文本中提取卷/期/页码
    if not paper.volume or not paper.issue or not paper.pages:
        # 查找包含年卷期页信息的文本
        info_texts = soup.select(".top-space, .rowtit, .p01")
        for el in info_texts:
            text = el.get_text(strip=True)
            # 匹配模式: 2023,45(3):123-130 或 2023年 第45卷 第3期
            m = re.search(r'(\d{4})[,，\s]*(\d+)[(（](\d+)[)）][:：]\s*(\d+[-–]\d+)', text)
            if m:
                if not paper.year:
                    paper.year = m.group(1)
                if not paper.volume:
                    paper.volume = m.group(2)
                if not paper.issue:
                    paper.issue = m.group(3)
                if not paper.pages:
                    paper.pages = m.group(4).replace("–", "-")
                break

    # PDF URL
    pdf = soup.select_one(S["pdf_download"]) or soup.select_one(S["pdf_download_alt"])
    if pdf:
        href = pdf.get("href", "")
        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = "https://kns.cnki.net" + href
        paper.pdf_url = href
    else:
        for a in soup.select("a[href*='bar.cnki.net']"):
            href = a.get("href", "")
            if href:
                paper.pdf_url = href
                break

    paper.detail_fetched = True
    return paper


def normalize_title(title):
    """标准化标题用于模糊匹配：去除标签、合并空白"""
    t = re.sub(r'<[^>]+>', '', title)
    t = re.sub(r'\s+', '', t)
    t = re.sub(r'[\u3000\u00a0]', '', t)
    return t.lower().strip()


def match_paper(search_results, target_title, threshold=0.6):
    """通过标题相似度从搜索结果中匹配最佳论文。

    使用字符集Jaccard相似度 + 长度比率加权。

    Returns: 匹配的论文字典或None
    """
    norm_target = normalize_title(target_title)
    if not norm_target:
        return None

    best_match = None
    best_score = 0.0

    for paper in search_results:
        norm_candidate = normalize_title(paper.get("title", ""))
        if not norm_candidate:
            continue

        if norm_candidate == norm_target:
            return paper

        target_chars = set(norm_target)
        candidate_chars = set(norm_candidate)
        if not target_chars or not candidate_chars:
            continue

        intersection = target_chars & candidate_chars
        union = target_chars | candidate_chars
        score = len(intersection) / len(union) if union else 0

        len_ratio = min(len(norm_candidate), len(norm_target)) / max(len(norm_candidate), len(norm_target))
        score = score * 0.6 + len_ratio * 0.4

        if score > best_score:
            best_score = score
            best_match = paper

    if best_score >= threshold:
        return best_match
    return None
