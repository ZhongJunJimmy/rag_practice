"""
查詢改寫相關函數 (Query Rewrite / HyDE)
"""
from typing import Literal

from libs.config import CHAT_MODEL, MID_CHAT_MODEL
from libs.ollama_client import client
from config.prompts import QUERY_REWRITE_PROMPT, HYDE_PROMPT


def rewrite_query(query: str) -> list[str]:
    """改寫查詢以更適合文件檢索，回傳中文與英文版本"""
    prompt = QUERY_REWRITE_PROMPT.format(query=query)

    res = client.chat(
        model=MID_CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    content = res["message"]["content"].strip()
    # 分割行並移除空白行
    queries = [line.strip() for line in content.splitlines() if line.strip()]
    return queries[:2]


def hyde_query(query: str) -> str:
    """使用 HyDE 方法生成假想文件內容"""
    prompt = HYDE_PROMPT.format(query=query)

    res = client.chat(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return res["message"]["content"].strip()


def build_search_query(query: str, mode: Literal["none", "rewrite", "hyde"]) -> list[str]:
    """根據模式構建搜尋查詢，回傳查詢列表"""
    if mode == "rewrite":
        return rewrite_query(query)
    if mode == "hyde":
        return [hyde_query(query)]
    return [query]
