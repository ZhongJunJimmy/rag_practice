"""
嵌入向量、快取和索引相關函數
"""
from pathlib import Path
from typing import Any, Dict, List
import json

import numpy as np

from libs.config import EMBED_MODEL
from libs.ollama_client import embedd_client


def embed_text(text: str) -> np.ndarray:
    """使用 Ollama 生成嵌入向量"""
    response = embedd_client.embed(model=EMBED_MODEL, input=text)
    return np.array(response["embeddings"][0], dtype=np.float32)


def load_cache(cache_path: Path) -> Dict[str, Any]:
    """載入快取"""
    if not cache_path.exists():
        return {}
    return json.loads(cache_path.read_text(encoding="utf-8"))


def save_cache(cache: Dict[str, Any], cache_path: Path) -> None:
    """保存快取"""
    cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


def build_index_with_cache(chunks: List[Dict[str, Any]], cache_path: Path) -> List[Dict[str, Any]]:
    """使用快取構建索引"""
    cache = load_cache(cache_path)
    updated = False
    index = []

    for chunk in chunks:
        key = f"{chunk['source']}::{chunk['chunk_id']}::{chunk['text']}"
        if key in cache:
            vec = np.array(cache[key], dtype=np.float32)
        else:
            vec = embed_text(chunk["text"])
            cache[key] = vec.tolist()
            updated = True

        index.append({**chunk, "embedding": vec})

    if updated:
        save_cache(cache, cache_path)

    return index


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """計算餘弦相似度"""
    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)
    if a_norm == 0 or b_norm == 0:
        return 0.0
    return float(np.dot(a, b) / (a_norm * b_norm))
