"""
環境設定與 config.json 讀取
"""
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config.json"


def load_config(path: Path = CONFIG_PATH) -> dict:
    """讀取專案根目錄 config 目錄中的 config.json。"""
    if not path.exists():
        raise RuntimeError(f"配置檔 {path} 不存在。請建立 config/config.json。")

    return json.loads(path.read_text(encoding="utf-8"))


CONFIG = load_config()

OLLAMA_HOST = CONFIG.get("OLLAMA_HOST")
if not OLLAMA_HOST:
    raise RuntimeError("OLLAMA_HOST is not set in config.json.")

DATA_DIR = Path(CONFIG.get("DATA_DIR", "data"))
CACHE_PATH = Path(CONFIG.get("CACHE_PATH", "cache/embeddings.json"))

EMBED_MODEL = CONFIG.get("EMBED_MODEL", "nomic-embed-text")
CHAT_MODEL = CONFIG.get("CHAT_MODEL", "qwen3:4b")

MAX_CHARS = int(CONFIG.get("MAX_CHARS", 800))
TOP_K_RETRIEVE = int(CONFIG.get("TOP_K_RETRIEVE", 8))
TOP_K_FINAL = int(CONFIG.get("TOP_K_FINAL", 3))
