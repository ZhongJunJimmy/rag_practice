"""
檢索和重排序相關函數
"""
from typing import Any, Dict, List
import re
import numpy as np
from ollama import Client

from libs.config import CHAT_MODEL, OLLAMA_HOST, TOP_K_RETRIEVE, TOP_K_FINAL
from .embedding import cosine_similarity, embed_text

client = Client(host=OLLAMA_HOST)


def retrieve(search_query: str, index: List[Dict[str, Any]], top_k: int = TOP_K_RETRIEVE) -> List[Dict[str, Any]]:
    """檢索最相關的文件塊"""
    q_vec = embed_text(search_query)
    scored = []

    for item in index:
        score = cosine_similarity(q_vec, item["embedding"])
        scored.append({**item, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def rerank(query: str, candidates: List[Dict[str, Any]], top_k: int = TOP_K_FINAL) -> List[Dict[str, Any]]:
    """使用 LLM 重新排序候選項"""
    rescored = []

    for item in candidates:
        prompt = f"""
你是文件檢索重排序器。
請評估「問題」與「文件片段」的相關性，輸出 0 到 10 的整數分數即可。
不要解釋，不要輸出其他文字。

【問題】
{query}

【文件片段】
{item['text']}
""".strip()

        res = client.chat(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = res["message"]["content"].strip()

        m = re.search(r"\d+", raw)
        score = int(m.group()) if m else 0

        rescored.append({**item, "score": float(score)})

    rescored.sort(key=lambda x: x["score"], reverse=True)
    print([x["score"] for x in rescored[:top_k]])
    return rescored[:top_k]
