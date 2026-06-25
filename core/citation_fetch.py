"""CNKI Desktop - 引用获取模块

根据 cnki.md 提供的引用按钮 HTML 结构实现引用获取功能。
"""
import time
from bs4 import BeautifulSoup


def fetch_citation(page, paper_index: int) -> str:
    """通过点击引用按钮获取 GB/T 7714-2025 格式引文。
    
    Args:
        page: Playwright Page对象（需在搜索结果页）
        paper_index: 论文在结果列表中的索引（从1开始，对应 data-cur 属性）
    
    Returns:
        GB/T 7714-2025 格式引文文本，失败返回空字符串
    """
    try:
        # 1. 找到对应论文行的引用按钮
        # 根据 cnki.md: <a class="icon-quote" title="引用" href="javascript:void(0)"><i></i></a>
        row_selector = f"tr input.cbItem[data-cur='{paper_index}']"
        checkbox = page.query_selector(row_selector)
        if not checkbox:
            return ""
        
        # 找到同一行的引用按钮
        row = checkbox.evaluate_handle("el => el.closest('tr')")
        quote_btn = row.query_selector("a.icon-quote")
        if not quote_btn:
            # 尝试其他选择器
            quote_btn = row.query_selector("a[title='引用']")
        
        if not quote_btn:
            return ""
        
        # 2. 点击引用按钮
        quote_btn.click()
        time.sleep(1)
        
        # 3. 等待弹窗出现并提取引文
        # 根据 cnki.md: <td class="quote-r">GB/T 7714-2025 格式引文</td>
        quote_r = page.query_selector(".quote-r")
        if quote_r:
            citation_text = quote_r.inner_text()
            # 关闭弹窗（点击关闭按钮或弹窗外部）
            close_btn = page.query_selector(".quote-close, .close-btn, [aria-label='关闭']")
            if close_btn:
                close_btn.click()
            else:
                # 点击弹窗外部关闭
                page.mouse.click(0, 0)
            return citation_text.strip()
        
        # 尝试其他选择器
        citation_elem = page.query_selector(".citation-text, #citationText")
        if citation_elem:
            citation_text = citation_elem.inner_text()
            # 关闭弹窗
            page.mouse.click(0, 0)
            return citation_text.strip()
        
        return ""
    except Exception as e:
        print(f"获取引用失败: {e}")
        return ""


def fetch_citations_batch(page, papers: list, callback=None) -> dict:
    """批量获取引用。
    
    Args:
        page: Playwright Page对象（需在搜索结果页）
        papers: Paper对象列表
        callback: 进度回调函数 callback(index, total, citation_text)
    
    Returns:
        dict: {paper_index: citation_text}
    """
    results = {}
    total = len(papers)
    
    for i, paper in enumerate(papers):
        # 根据 paper 在搜索结果中的位置获取引用
        # 需要从 paper 对象中获取其在列表中的索引
        paper_index = getattr(paper, 'result_index', i + 1)
        
        citation = fetch_citation(page, paper_index)
        results[i] = citation
        
        if callback:
            callback(i + 1, total, citation)
        
        # 控制请求频率
        time.sleep(0.5)
    
    return results


def parse_citation_from_html(html: str) -> str:
    """从HTML中解析引用文本（备用方法）。
    
    Args:
        html: 包含引用弹窗的HTML内容
    
    Returns:
        引用文本
    """
    soup = BeautifulSoup(html, "lxml")
    quote_r = soup.select_one(".quote-r")
    if quote_r:
        return quote_r.get_text(strip=True)
    
    citation_elem = soup.select_one(".citation-text, #citationText")
    if citation_elem:
        return citation_elem.get_text(strip=True)
    
    return ""