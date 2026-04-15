"""
檔案處理器，負責不同格式檔案的文本提取
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import PyPDF2
from libs.utils import read_markdown, normalize_text

class BaseProcessor(ABC):
    """處理器基類"""
    @abstractmethod
    def extract_text(self, path: Path) -> str:
        """提取檔案中的文本"""
        pass

class MarkdownProcessor(BaseProcessor):
    """Markdown 檔案處理器"""
    def extract_text(self, path: Path) -> str:
        text = read_markdown(path)
        return normalize_text(text)

class PdfProcessor(BaseProcessor):
    """PDF 檔案處理器"""
    def extract_text(self, path: Path) -> str:
        text = ""
        try:
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                if reader.is_encrypted:
                    reader.decrypt("YOUR_PASSWROD")
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Error reading PDF {path}: {e}")
        return normalize_text(text)

def get_processor(path: Path) -> Optional[BaseProcessor]:
    """根據檔案擴展名獲取對應的處理器"""
    ext = path.suffix.lower()
    if ext == ".md":
        return MarkdownProcessor()
    elif ext == ".pdf":
        return PdfProcessor()
    return None