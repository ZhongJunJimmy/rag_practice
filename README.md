# RAG Project

一個基於本地 Ollama 的 RAG (Retrieval-Augmented Generation) 應用，用於學習和實作 RAG 的基礎概念。採用 PostgreSQL 進行持久化存儲，使用 pgvector 進行高效的向量搜索。

## 專案概述

這個專案實現了一個完整的 RAG 系統，包含以下核心組件：
- **文件分塊**：將 Markdown 文件按標題和段落分割
- **嵌入生成**：使用 Ollama 的嵌入模型生成向量，並存儲至 PostgreSQL
- **向量檢索**：基於 pgvector 的高效向量搜索
- **重排序**：使用 LLM 進行結果智能重排序
- **答案生成**：基於檢索結果生成回答
- **持久化存儲**：使用 PostgreSQL 管理文件、分塊和向量

## 主要功能

- 自動處理 Markdown 文件並分塊
- 使用 Ollama 生成高質量文本嵌入
- 向量嵌入持久化存儲到 PostgreSQL
- 基於 pgvector 的高效語意檢索
- 查詢改寫和 HyDE 支持
- LLM 驅動的智能重排序
- RESTful API 接口
- 統一配置管理
- 環境變數安全管理

## 專案結構

```
rag_project/
├── .env                  # 環境變數（包含 OLLAMA_API_KEY）
├── .gitignore            # Git 忽略文件
├── app.py                # FastAPI 主應用程式
├── libs/
│   ├── config.py         # 配置管理
│   ├── db.py             # PostgreSQL 連接池管理
│   ├── ollama_client.py  # 共享 Ollama 客戶端實例
│   └── utils.py          # 工具函數
├── services/
│   ├── chunking.py       # 文件分塊服務
│   ├── embedding.py      # 嵌入向量服務
│   ├── query.py          # 查詢處理服務
│   ├── retrieval.py      # 檢索和重排序服務
│   ├── answer.py         # 答案生成服務
│   └── storage.py        # 數據庫操作服務
├── config/
│   └── config.json       # 配置文件
├── cache/
│   └── embeddings.json   # (保留作為備份) 嵌入向量快取
├── data/                 # Markdown 文件存放目錄
├── requirements.txt      # Python 依賴列表
└── README.md
```

## 配置

### 環境變數 (.env)

在項目根目錄創建 `.env` 文件用於存儲敏感信息：

```
OLLAMA_API_KEY=your_api_key_here
```

### 主配置 (config/config.json)

編輯 `config/config.json` 來調整設定：

```json
{
  "OLLAMA_HOST": "http://127.0.0.1:11434",
  "DATA_DIR": "data",
  "CACHE_PATH": "cache/embeddings.json",
  "EMBED_MODEL": "embeddinggemma",
  "CHAT_MODEL": "gemma4:31b",
  "MAX_CHARS": 800,
  "TOP_K_RETRIEVE": 8,
  "TOP_K_FINAL": 3,
  "PG_DSN": "postgresql://rag_user:rag_password@localhost:5432/rag_db",
  "VECTOR_DIM": 768
}
```

**配置說明**：
- `OLLAMA_HOST`: Ollama 服務地址
- `DATA_DIR`: Markdown 文件存放目錄
- `EMBED_MODEL`: 嵌入模型名稱
- `CHAT_MODEL`: 聊天和重排序使用的模型
- `PG_DSN`: PostgreSQL 連接字符串
- `VECTOR_DIM`: 向量維度（應與嵌入模型輸出維度相匹配）

## 安裝與使用

### 環境需求

- Python 3.8+
- Ollama (運行中)
- PostgreSQL 12+（已安裝 pgvector 擴展）

### 安裝步驟

1. **安裝依賴**：
   ```bash
   pip install -r requirements.txt
   ```

2. **配置環境變數**：
   - 複製或創建 `.env` 文件
   - 設置 `OLLAMA_API_KEY` 和其他敏感信息

3. **配置 PostgreSQL**：
   - 確保 PostgreSQL 正常運行
   - 創建數據庫並安裝 pgvector 擴展：
     ```bash
     createdb rag_db
     psql -d rag_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
     ```
   - 更新 `config.json` 中的 `PG_DSN` 連接字符串

4. **初始化數據庫**：
   ```bash
   python -c "from libs.db import init_db; init_db()"
   ```

5. **啟動 Ollama**：
   ```bash
   ollama serve
   ```

6. **下載模型**：
   ```bash
   ollama pull embeddinggemma
   ollama pull gemma4:31b
   ```

7. **運行應用程式**：
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
2. **嵌入技術**：文本到向量的轉換與存儲
3. **向量數據庫**：PostgreSQL + pgvector 進行高效的向量搜索
4. **持久化設計**：分離的 Ollama 客戶端、連接池管理
5. **查詢優化**：Rewrite 和 HyDE 技術
6. **答案生成**：基於檢索結果的生成式回應
7. **配置管理**：環境變數和 JSON 配置的統一管理
8. **安全最佳實踐**：敏感信息存儲在 `.env` 文件

## 開發歷程

專案從單一 `app.py` 文件開始，逐步重構為完整的生產級架構：

1. **初始版本**：所有功能集中在單一文件中
2. **模組化**：按功能將代碼分成多個模組
3. **資料夾組織**：將模組放入 `libs/` 和 `services/` 目錄
4. **配置統一**：將硬編碼常數移至 `config.json`
5. **環境變數管理**：敏感信息存儲在 `.env` 文件
6. **資源共享**：Ollama 客戶端分離出單一實例 (`libs/ollama_client.py`)
7. **持久化存儲**：從記憶體快取升級到 PostgreSQL + pgvector
8. **連接池管理**：添加 `libs/db.py` 實現數據庫連接池

## 架構改進

### Ollama 客戶端分離

所有的 Ollama 連接通過 `libs/ollama_client.py` 進行管理，確保：
- 單一責任原則：統一的客戶端配置
- 資源複用：避免重複創建連接
- 易於維護：配置變更只需修改一處
- 環境變數支持：API Key 從 `.env` 讀取

### PostgreSQL + pgvector 集成

向量嵌入持久化存儲提供：
- 高效檢索：原生向量操作支持
- 可擴展性：支持大規模文檔和向量存儲
- 持久化：重啟後無數據丟失
- 事務支持：確保數據一致性

### 依賴注入模式

所有服務模組通過統一配置管理外部依賴：
- 數據庫連接池（`libs/db.py`）
- Ollama 客戶端實例（`libs/ollama_client.py`）
- 配置參數（`libs/config.py`）

## 後續發展

想了解後續的改進計劃？查看 [RAG 強化路徑 Roadmap](./ROADMAP.md)

Roadmap 包含 5 個階段的 15 項改進計劃，從 Retrieval 強化到完整的 Agentic 系統。

## 授權

MIT License
