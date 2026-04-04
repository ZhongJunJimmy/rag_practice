# RAG Project

一個基於本地 Ollama 的 RAG (Retrieval-Augmented Generation) 應用程式，用於學習和實作 RAG 的基礎概念。

## 專案概述

這個專案實現了一個簡單的 RAG 系統，包含以下核心組件：
- **文件分塊**：將 Markdown 文件按標題和段落分割
- **嵌入生成**：使用 Ollama 的嵌入模型生成向量
- **檢索**：基於餘弦相似度的向量檢索
- **重排序**：使用 LLM 進行結果重排序
- **答案生成**：基於檢索結果生成回答

## 主要功能

- 自動處理 Markdown 文件並分塊
- 語意檢索與向量嵌入
- 查詢改寫和 HyDE 支持
- LLM 驅動的重排序
- RESTful API 接口
- 統一配置管理

## 專案結構

```
rag_project/
├── .gitignore            # Git 忽略文件
├── app.py                 # FastAPI 主應用程式
├── libs/
│   ├── config.py         # 配置管理
│   └── utils.py          # 工具函數
├── services/
│   ├── chunking.py      # 文件分塊服務
│   ├── embedding.py     # 嵌入向量服務
│   ├── query.py         # 查詢處理服務
│   ├── retrieval.py     # 檢索服務
│   └── answer.py        # 答案生成服務
├── config/
│   └── config.json      # 配置文件
├── cache/
│   └── embeddings.json  # 嵌入向量快取
├── data/                 # Markdown 文件存放目錄
├── requirements.txt      # Python 依賴列表
└── README.md
```

## 配置

編輯 `config/config.json` 來調整設定：

```json
{
  "OLLAMA_HOST": "http://127.0.0.1:11434",
  "DATA_DIR": "data",
  "CACHE_PATH": "cache/embeddings.json",
  "EMBED_MODEL": "nomic-embed-text",
  "CHAT_MODEL": "qwen3:4b",
  "MAX_CHARS": 800,
  "TOP_K_RETRIEVE": 8,
  "TOP_K_FINAL": 3
}
```

## 安裝與使用

### 環境需求

- Python 3.8+
- Ollama (運行中)

### 安裝步驟

1. **安裝依賴**：
   ```bash
   pip install -r requirements.txt
   ```

2. **啟動 Ollama**：
   ```bash
   ollama serve
   ```

3. **下載模型**：
   ```bash
   ollama pull nomic-embed-text
   ollama pull qwen3:4b
   ```

4. **運行應用程式**：
   ```bash
   uvicorn app:app --reload
   ```

### API 使用

#### 健康檢查
```bash
GET /health
```

#### 問答接口
```bash
POST /ask
Content-Type: application/json

{
  "query": "你的問題",
  "mode": "none"  // 或 "rewrite", "hyde"
}
```

## 學習重點

這個專案涵蓋了 RAG 系統的核心概念：

1. **文件處理**：Markdown 解析和智能分塊
2. **嵌入技術**：文本到向量的轉換
3. **向量檢索**：高效的相似度搜索
4. **查詢優化**：改寫和 HyDE 技術
5. **答案生成**：基於檢索結果的生成式回應
6. **配置管理**：統一的設定系統

## 開發歷程

專案從單一 `app.py` 文件開始，逐步重構為模組化架構：

1. **初始版本**：所有功能集中在單一文件中
2. **模組化**：按功能將代碼分成多個模組
3. **資料夾組織**：將模組放入 `libs/` 和 `services/` 目錄
4. **配置統一**：將硬編碼常數移至 `config.json`
5. **環境變數**：從 `.env` 遷移到 JSON 配置

## 貢獻

歡迎提交 Issue 和 Pull Request！

## 授權

MIT License