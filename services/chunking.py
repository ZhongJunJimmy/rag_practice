"""
Markdown 檔案分塊相關函數
"""
from pathlib import Path
from typing import List, Dict, Any
import re

from libs.config import MAX_CHARS
from libs.utils import read_markdown, normalize_text, split_paragraphs


def chunk_markdown_by_heading(md_text: str) -> List[Dict[str, Any]]:
    """根據 Markdown 標題分塊"""
    lines = md_text.splitlines()

    sections: List[Dict[str, Any]] = []
    current_lines: List[str] = []
    current_title: str | None = None
    current_level: int | None = None
    heading_stack: List[str] = []

    for line in lines:
        match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if match:
            if current_lines:
                sections.append({
                    "title": current_title,
                    "level": current_level,
                    "path": " > ".join(heading_stack),
                    "text": "\n".join(current_lines).strip(),
                })

            current_level = len(match.group(1))
            current_title = match.group(2).strip()
            heading_stack = heading_stack[:current_level - 1]
            heading_stack.append(current_title)
            current_lines = [line]
        else:
            if current_lines:
                current_lines.append(line)

    if current_lines:
        sections.append({
            "title": current_title,
            "level": current_level,
            "path": " > ".join(heading_stack),
            "text": "\n".join(current_lines).strip(),
        })

    return sections


def split_large_section(section: Dict[str, Any], max_chars: int = MAX_CHARS) -> List[Dict[str, Any]]:
    """將大型章節分割成較小的塊"""
    text = section["text"]
    if len(text) <= max_chars:
        return [section]

    paragraphs = split_paragraphs(text)
    if len(paragraphs) <= 1:
        return [section]

    chunks: List[Dict[str, Any]] = []
    buf: List[str] = []
    buf_len = 0
    part_no = 1

    for p in paragraphs:
        p_len = len(p)
        if buf and buf_len + p_len + 2 > max_chars:
            c = dict(section)
            c["text"] = "\n\n".join(buf)
            c["part"] = part_no
            chunks.append(c)
            part_no += 1
            buf = [p]
            buf_len = p_len
        else:
            buf.append(p)
            buf_len += p_len + (2 if buf_len > 0 else 0)

    if buf:
        c = dict(section)
        c["text"] = "\n\n".join(buf)
        c["part"] = part_no
        chunks.append(c)

    return chunks


def build_chunks(md_text: str, source_name: str) -> List[Dict[str, Any]]:
    """構建完整的分塊結構"""
    sections = chunk_markdown_by_heading(md_text)
    final_chunks: List[Dict[str, Any]] = []
    counter = 1

    for sec in sections:
        sub_chunks = split_large_section(sec)
        for sub in sub_chunks:
            final_chunks.append({
                "chunk_id": f"{Path(source_name).stem}_{counter:04d}",
                "source": source_name,
                "title": sub.get("title"),
                "level": sub.get("level"),
                "path": sub.get("path"),
                "part": sub.get("part", 1),
                "text": sub.get("text", "").strip(),
            })
            counter += 1

    return final_chunks


def load_all_markdown_files(data_dir: Path) -> List[Dict[str, Any]]:
    """載入所有 Markdown 檔案並分塊"""
    all_chunks: List[Dict[str, Any]] = []
    for md_file in sorted(data_dir.glob("*.md")):
        md_text = normalize_text(read_markdown(md_file))
        all_chunks.extend(build_chunks(md_text, md_file.name))
    return all_chunks
