"""
答案生成相關函數
"""
from typing import Any, Dict, List

from libs.config import CHAT_MODEL
from libs.ollama_client import client
from config.prompts import ANSWER_PROMPT


def build_answer_prompt(query: str, docs: List[Dict[str, Any]]) -> str:
    """構建答案生成的提示詞"""
    context = "\n\n".join(
        [
            f"[source={d['source']} | chunk_id={d['chunk_id']} | path={d['file_path']}]\n{d['text']}"
            for d in docs
        ]
    )

    return ANSWER_PROMPT.format(context=context, query=query)


def answer_question(query: str, docs: List[Dict[str, Any]]) -> str:
    """根據檢索到的文件生成答案"""
    prompt = build_answer_prompt(query, docs)
    
    # 簡單的長度檢查，避免 prompt 過長 (例如限制在 12000 字左右)
    if len(prompt) > 12000:
        # 如果太長，嘗試減少參考資料數量
        docs = docs[:max(1, len(docs)//2)]
        prompt = build_answer_prompt(query, docs)

    res = client.chat(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"num_ctx": 8192},
    )
    return res["message"]["content"]
