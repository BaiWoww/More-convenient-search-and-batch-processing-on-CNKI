"""
CNKI Desktop - GB/T 7714-2025 引文格式化模块
"""
from typing import List


def format_authors(authors: List[str], max_authors: int = 3) -> str:
    """按GB/T 7714-2025格式化作者列表。
    最多列出3位作者，超过则加", 等"。
    """
    if not authors:
        return "[作者不详]"
    if len(authors) <= max_authors:
        return ", ".join(authors)
    return ", ".join(authors[:max_authors]) + ", 等"


def format_citation(paper, seq: int) -> str:
    """根据论文类型生成GB/T 7714-2025格式引文。

    Args:
        paper: Paper对象 (需包含 title, authors, journal, year, volume, issue, pages, doi, doc_type 等)
        seq: 序号

    Returns:
        格式化引文字符串
    """
    doc_type = getattr(paper, 'doc_type', '') or _infer_doc_type(paper)

    if doc_type == "J":
        return _format_journal(paper, seq)
    elif doc_type == "D":
        return _format_thesis(paper, seq)
    elif doc_type == "C":
        return _format_conference(paper, seq)
    elif doc_type == "N":
        return _format_newspaper(paper, seq)
    elif doc_type == "P":
        return _format_patent(paper, seq)
    elif doc_type == "S":
        return _format_standard(paper, seq)
    else:
        return _format_generic(paper, seq)


def _get(paper, attr, default=""):
    """安全获取Paper属性"""
    val = getattr(paper, attr, default) if hasattr(paper, attr) else default
    if isinstance(val, list):
        return val
    return val or default


def _infer_doc_type(paper):
    """从dbname或classid推断文献类型"""
    dbname = _get(paper, 'dbname', '')
    search_classid = _get(paper, 'search_classid', '')
    code = search_classid or dbname

    type_map = {
        "YSTT4HG0": "J",
        "LSTPFY1C": "D",
        "LSTPY0F2": "D",
        "JUP3MUPD": "C",
        "CCND": "N",
        "CYFD": "A",
        "SCOD": "P",
        "CISD": "S",
    }
    return type_map.get(code, "")


def _format_journal(p, seq: int) -> str:
    """期刊论文: [序号] 作者. 篇名[J]. 刊名, 年, 卷(期): 页码."""
    authors = format_authors(_get(p, 'authors', []))
    title = _get(p, 'title', '[篇名不详]')
    journal = _get(p, 'journal', '[刊名不详]')
    year = _get(p, 'year', '')
    volume = _get(p, 'volume', '')
    issue = _get(p, 'issue', '')
    pages = _get(p, 'pages', '')
    doi = _get(p, 'doi', '')

    # 构建引文
    result = f"[{seq}] {authors}. {title}[J]. {journal}"
    if year:
        result += f", {year}"
    if volume:
        result += f", {volume}"
    if issue:
        result += f"({issue})"
    if pages:
        result += f": {pages}"
    result += "."
    if doi:
        result += f" DOI: {doi}."
    return result


def _format_thesis(p, seq: int) -> str:
    """学位论文: [序号] 作者. 篇名[D]. 保存单位, 年."""
    authors = format_authors(_get(p, 'authors', []))
    title = _get(p, 'title', '[篇名不详]')
    institutions = _get(p, 'institutions', [])
    institution = institutions[0] if institutions else "[单位不详]"
    year = _get(p, 'year', '')

    return f"[{seq}] {authors}. {title}[D]. {institution}, {year}."


def _format_conference(p, seq: int) -> str:
    """会议论文: [序号] 作者. 篇名[C]//会议名. 出版地: 出版者, 年: 页码."""
    authors = format_authors(_get(p, 'authors', []))
    title = _get(p, 'title', '[篇名不详]')
    journal = _get(p, 'journal', '[会议名不详]')
    year = _get(p, 'year', '')
    pages = _get(p, 'pages', '')
    institutions = _get(p, 'institutions', [])

    result = f"[{seq}] {authors}. {title}[C]//{journal}"
    if institutions:
        result += f". {institutions[0]}"
    if year:
        result += f", {year}"
    if pages:
        result += f": {pages}"
    result += "."
    return result


def _format_newspaper(p, seq: int) -> str:
    """报纸: [序号] 作者. 篇名[N]. 报纸名, 出版日期."""
    authors = format_authors(_get(p, 'authors', []))
    title = _get(p, 'title', '[篇名不详]')
    journal = _get(p, 'journal', '[报纸名不详]')
    date = _get(p, 'date', '')

    return f"[{seq}] {authors}. {title}[N]. {journal}, {date}."


def _format_patent(p, seq: int) -> str:
    """专利: [序号] 发明人. 专利名[P]. 专利号, 公告日期."""
    authors = format_authors(_get(p, 'authors', []))
    title = _get(p, 'title', '[篇名不详]')
    doi = _get(p, 'doi', '')
    date = _get(p, 'date', '')

    return f"[{seq}] {authors}. {title}[P]. {doi}, {date}."


def _format_standard(p, seq: int) -> str:
    """标准: [序号] 标准编号, 标准名称[S]."""
    title = _get(p, 'title', '[标准名称不详]')
    doi = _get(p, 'doi', '')
    year = _get(p, 'year', '')

    if doi:
        return f"[{seq}] {doi}, {title}[S]. {year}."
    return f"[{seq}] {title}[S]. {year}."


def _format_generic(p, seq: int) -> str:
    """通用格式 (未知类型)"""
    authors = format_authors(_get(p, 'authors', []))
    title = _get(p, 'title', '[篇名不详]')
    journal = _get(p, 'journal', '')
    year = _get(p, 'year', '')

    result = f"[{seq}] {authors}. {title}[M]"
    if journal:
        result += f". {journal}"
    if year:
        result += f", {year}"
    result += "."
    return result


def format_citations_batch(papers: list, start_seq: int = 1) -> str:
    """批量格式化引文。

    Args:
        papers: Paper对象列表
        start_seq: 起始序号

    Returns:
        多行引文字符串
    """
    lines = []
    for i, p in enumerate(papers, start_seq):
        lines.append(format_citation(p, i))
    return "\n".join(lines)
