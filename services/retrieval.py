"""
檢索和重排序相關函數
"""
from typing import Any, Dict, List
import re
import numpy as np
import time

from libs.config import TOP_K_RETRIEVE, TOP_K_FINAL, MID_CHAT_MODEL
from libs.ollama_client import client
from config.prompts import RERANK_PROMPT
from .embedding import cosine_similarity, embed_text
import time


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
        prompt = RERANK_PROMPT.format(query=query, text=item['text'])
        res = client.chat(
            model=MID_CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = res["message"]["content"].strip()

        m = re.search(r"\d+", raw)
        score = int(m.group()) if m else 0

        rescored.append({**item, "score": float(score)})

    rescored.sort(key=lambda x: x["score"], reverse=True)
    return rescored[:top_k]