"""
查詢改寫相關函數 (Query Rewrite / HyDE)
"""
from typing import Literal

from libs.config import CHAT_MODEL
from libs.ollama_client import client


def rewrite_query(query: str) -> list[str]:
    """改寫查詢以更適合文件檢索，回傳中文與英文版本"""
    prompt = f"""
請將以下使用者問題改寫成更適合文件檢索的查詢語句。
要求：
1. 保留原意
2. 補足可能的專有名詞
3. 不要回答問題
4. 請分兩行提供：第一行為繁體中文改寫版本，第二行為英文改寫版本。不要加上任何標記（如 "中文：" 或 "1."）。

問題：
{query}
""".strip()

    res = client.chat(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    content = res["message"]["content"].strip()
    # 分割行並移除空白行
    queries = [line.strip() for line in content.splitlines() if line.strip()]
    return queries[:2]


def hyde_query(query: str) -> str:
    """使用 HyDE 方法生成假想文件內容"""
    prompt = f"""
根據以下問題，生成一段適合用來做語意檢索的假想文件內容。
要求：
1. 內容看起來像知識文件的一小段說明
2. 不要寫成聊天口吻
3. 用繁體中文
4. 長度 80 到 150 字

問題：
{query}
""".strip()

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
