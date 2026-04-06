# RAG 強化路徑 Roadmap

## 當前狀態
- Base RAG
- Query Rewrite
- HyDE
- Rerank

---

## Phase 1：Retrieval 強化（優先）

### 1. Hybrid Search
- 實作 vector + keyword (BM25 / full-text)
- query 同時跑：
  - original query
  - rewrite query
  - HyDE query
- 合併結果（score fusion）
- 再進 rerank

### 2. Parent-Child Chunk Retrieval
- 文件切分：
  - parent chunk（大段）
  - child chunk（小段）
- 檢索 child → 回傳 parent
- 解決：
  - chunk 太小失上下文
  - chunk 太大不精準

### 3. Metadata Filtering
- 建立 metadata schema：
  - product
  - version
  - doc_type
  - timestamp
- retrieval 加 filter 條件
- 避免：
  - 不同版本混用
  - 錯誤文件來源

---

## Phase 2：答案可信度提升

### 4. Citation / Grounding
- 回傳：
  - answer
  - sources
  - chunk reference
- 每段答案要能對應來源
- 限制模型只能用提供 context

### 5. Unsupported Answer Detection
- 判斷條件：
  - similarity score 過低
  - rerank score 過低
  - 無法對應 citation
- fallback：
  - 回答「找不到足夠資訊」
  - 提示使用者改問

### 6. Confidence Scoring
- 計算：
  - retrieval score
  - rerank score
  - citation coverage
- 回傳 confidence
- 可用於 UI 或 decision logic

---

## Phase 3：工程化與評估

### 7. Evaluation Dataset
- 建立 benchmark dataset：
  - 50~200 題
- 標註：
  - 正確答案
  - relevant docs
  - 是否可回答
- 評估：
  - Recall@K
  - MRR / nDCG
  - answer correctness
  - groundedness

### 8. Error Analysis Pipeline
- 記錄：
  - original query
  - rewrite / HyDE query
  - retrieved docs
  - reranked docs
  - final context
  - final answer
- 分析錯誤來源：
  - retrieval fail
  - rerank fail
  - generation hallucination

### 9. A/B Testing
- 比較不同 pipeline：
  - 有無 HyDE
  - 有無 rewrite
  - 不同 reranker
- 用 dataset 做 offline 評估

---

## Phase 4：處理複雜問題

### 10. Multi-hop Retrieval
- 流程：
  1. 初次 retrieval
  2. 從結果抽 keyword / entity
  3. 二次 retrieval
  4. 合併 context
- 用於：
  - 跨文件問題
  - 技術 troubleshooting

### 11. Query Intent Classification
- 分類：
  - fact lookup
  - summarization
  - comparison
  - troubleshooting
- 根據 intent 選 pipeline：
  - 不同 retrieval 策略
  - 不同 context size

### 12. Query Decomposition / Planning
- 將複雜問題拆解：
  - sub-queries
- 分別 retrieval
- 合併答案
- 適合：
  - 多條件問題
  - 比較問題

---

## Phase 5：進階系統（Agentic）

### 13. Tool Calling
- 整合：
  - SQL
  - API
  - log system
  - monitoring
- 判斷：
  - 是否需要外部資料
- 結合 retrieval + tools

### 14. Adaptive Pipeline
- 動態決策：
  - 是否使用 HyDE
  - 是否 rewrite
  - 是否 multi-hop
- 根據：
  - query complexity
  - retrieval confidence

### 15. Agentic RAG
- 加入 agent：
  - planning
  - tool selection
  - multi-step reasoning
- 組成：
  - retrieval + tools + LLM
- 變成完整 AI system
