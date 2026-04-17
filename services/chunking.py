"""
Markdown 檔案分塊相關函數
"""
from pathlib import Path
from typing import List, Dict, Any
import re
import fitz

from libs.config import MAX_CHARS
from libs.utils import normalize_text, split_paragraphs
from libs.processors import get_processor
from services.storage import get_document_password


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


def clean_pdf_text(text: str) -> str:
    """清理 PDF 提取的文字"""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]

    cleaned = []
    prev_empty = False

    for line in lines:
        if line == "":
            if prev_empty:
                continue
            prev_empty = True
        else:
            prev_empty = False
        cleaned.append(line)

    text = "\n".join(cleaned)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def is_pdf_heading(line: str) -> bool:
    """判斷是否為 PDF 標題"""
    line = line.strip()
    if not line or len(line) > 120:
        return False
    # 編號標題 (例如 1.1, 2.1.1)
    if re.match(r"^\d+(\.\d+)*[\s\-:：]+", line):
        return True
    return False


def chunk_pdf_file(pdf_path: Path, password: str = None) -> List[Dict[str, Any]]:
    """參考 pdf_chunking.py 的流程處理 PDF 分塊"""
    try:
        doc = fitz.open(pdf_path)
        if password:
            doc.authenticate(password)
    except Exception as e:
        print(f"無法開啟 PDF {pdf_path}: {e}")
        return []

    sections = []
    current = {
        "title": "UNKNOWN",
        "content": [],
        "page": None
    }

    for page_index, page in enumerate(doc):
        page_num = page_index + 1
        text = clean_pdf_text(page.get_text())

        if not text:
            continue

        lines = text.split("\n")
        for line in lines:
            if is_pdf_heading(line):
                if current["content"]:
                    sections.append({
                        "title": current["title"],
                        "content": "\n".join(current["content"]),
                        "page": current["page"]
                    })
                current = {
                    "title": line.strip(),
                    "content": [],
                    "page": page_num
                }
            else:
                current["content"].append(line)
                if current["page"] is None:
                    current["page"] = page_num

    if current["content"]:
        sections.append({
            "title": current["title"],
            "content": "\n".join(current["content"]),
            "page": current["page"]
        })
    doc.close()

    final_chunks = []
    counter = 1
    for sec in sections:
        # 1. Create Parent Chunk
        full_text = f"[Section: {sec['title']}]\n\n{sec['content']}"
        parent_id = f"{pdf_path.stem}_p{counter:04d}"
        
        final_chunks.append({
            "chunk_id": parent_id,
            "source": pdf_path.name,
            "title": sec["title"],
            "level": None,
            "path": None,
            "page": sec["page"],
            "part": 1,
            "text": full_text.strip(),
            "is_parent": True,
            "parent_id": None
        })
        
        # 2. Create Child Chunks
        chunk_size = MAX_CHARS
        overlap = 100
        start = 0
        child_counter = 1
        
        while start < len(full_text):
            end = start + chunk_size
            chunk_text = full_text[start:end]
            
            final_chunks.append({
                "chunk_id": f"{pdf_path.stem}_{counter:04d}_{child_counter:02d}",
                "source": pdf_path.name,
                "title": sec["title"],
                "level": None,
                "path": None,
                "page": sec["page"],
                "part": child_counter,
                "text": chunk_text.strip(),
                "is_parent": False,
                "parent_chunk_id": parent_id
            })
            child_counter += 1
            start += chunk_size - overlap
        
        counter += 1

    return final_chunks


def build_chunks(text: str, source_name: str) -> List[Dict[str, Any]]:
    """構建完整的分塊結構 (主要針對非 PDF 檔案)"""
    # 根據檔案擴展名決定分塊策略
    ext = Path(source_name).suffix.lower()
    
    if ext == ".md":
        sections = chunk_markdown_by_heading(text)
    else:
        # 對於其他非 Markdown 檔案，將整個文本視為一個章節
        sections = [{
            "title": None,
            "level": None,
            "path": None,
            "text": text,
        }]

    final_chunks: List[Dict[str, Any]] = []
    counter = 1

    for sec in sections:
        # 1. Create Parent Chunk
        parent_text = sec.get("text") or ""
        # Handle case where sec might be from chunk_markdown_by_heading (has "text") 
        # or a simple dict (has "text")
        parent_id = f"{Path(source_name).stem}_p{counter:04d}"
        
        final_chunks.append({
            "chunk_id": parent_id,
            "source": source_name,
            "title": sec.get("title"),
            "level": sec.get("level"),
            "path": sec.get("path"),
            "part": 1,
            "text": parent_text.strip(),
            "is_parent": True,
            "parent_id": None
        })

        # 2. Create Child Chunks
        sub_chunks = split_large_section(sec)
        for idx, sub in enumerate(sub_chunks, 1):
            final_chunks.append({
                "chunk_id": f"{Path(source_name).stem}_{counter:04d}_{idx:02d}",
                "source": source_name,
                "title": sub.get("title"),
                "level": sub.get("level"),
                "path": sub.get("path"),
                "part": sub.get("part", idx),
                "text": sub.get("text", "").strip(),
                "is_parent": False,
                "parent_chunk_id": parent_id
            })
        counter += 1

    return final_chunks


def load_all_files(data_dir: Path) -> List[Dict[str, Any]]:
    """載入所有支持的檔案並分塊"""
    all_chunks: List[Dict[str, Any]] = []
    
    # 支援的擴展名
    supported_extensions = [".md", ".pdf"]
    
    # 獲取所有符合條件的檔案
    files = []
    for ext in supported_extensions:
        files.extend(data_dir.glob(f"*{ext}"))
    
    for file_path in sorted(files):
        if file_path.suffix.lower() == ".pdf":
            # 使用專門的 PDF 分塊流程
            password = get_document_password(file_path.name)
            all_chunks.extend(chunk_pdf_file(file_path, password=password))
        else:
            processor = get_processor(file_path)
            if processor:
                text = processor.extract_text(file_path)
                all_chunks.extend(build_chunks(text, file_path.name))
            
    return all_chunks
