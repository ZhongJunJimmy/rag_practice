"""
答案生成相關函數
"""
from typing import Any, Dict, List
from ollama import Client

from libs.config import CHAT_MODEL, OLLAMA_HOST

client = Client(host=OLLAMA_HOST)


def build_answer_prompt(query: str, docs: List[Dict[str, Any]]) -> str:
    """構建答案生成的提示詞"""
    context = "\n\n".join(
        [
            f"[source={d['source']} | chunk_id={d['chunk_id']} | path={d['path']}]\n{d['text']}"
            for d in docs
        ]
    )

    return f"""
你是一個根據參考資料回答問題的助理。
規則：
1. 只能根據參考資料回答
2. 若資料不足，明確回答「資料不足，無法確認」
3. 不要自行補充參考資料沒有的事實
4. 使用繁體中文
5. 可簡短引用 chunk_id

【參考資料】
{context}

【問題】
{query}
""".strip()


def answer_question(query: str, docs: List[Dict[str, Any]]) -> str:
    """根據檢索到的文件生成答案"""
    prompt = build_answer_prompt(query, docs)
    res = client.chat(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return res["message"]["content"]
