"""
基本工具函數
"""
from pathlib import Path
from typing import List
import re


def ensure_dirs(data_dir: Path, cache_path: Path) -> None:
    """確保必要的目錄存在"""
    data_dir.mkdir(parents=True, exist_ok=True)
    cache_path.parent.mkdir(parents=True, exist_ok=True)


def read_markdown(path: Path) -> str:
    """讀取 Markdown 檔案"""
    return path.read_text(encoding="utf-8")


def normalize_text(text: str) -> str:
    """標準化文本換行符"""
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def split_paragraphs(text: str) -> List[str]:
    """根據段落分割文本"""
    parts = re.split(r"\n\s*\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]
