# Local RAG API

A Retrieval-Augmented Generation (RAG) application based on local Ollama, designed to implement a scalable and production-grade knowledge retrieval system. It utilizes FastAPI for the RESTful interface and PostgreSQL with pgvector for persistent vector storage, supporting various query optimization techniques.

## Project Overview

This project implements a complete RAG pipeline, covering the entire process from document processing to answer generation:

- **Multi-format Chunking**: Supports Markdown and PDF files, intelligently splitting them into a Parent-Child chunking structure.
- **Incremental Indexing**: Uses SHA256 hashes to track document and chunk content, regenerating embeddings only for modified content to significantly improve indexing efficiency.
- **Embedding Generation**: Integrates Ollama embedding models to convert text into high-dimensional vectors stored in PostgreSQL.
- **Advanced Retrieval**:
  - **Query Rewrite**: Rewrites user queries to expand semantic meaning.
  - **HyDE (Hypothetical Document Embeddings)**: Generates hypothetical answers to improve retrieval precision.
  - **pgvector Search**: Utilizes native PostgreSQL vector indexing for efficient similarity searches.
- **Intelligent Reranking**: Uses an LLM to perform a second, more precise sorting of the initial retrieval results.
- **Answer Generation**: Generates accurate responses based on the final filtered context.

## Project Structure

```
rag_project/
├── app.py                # FastAPI Main Application (API Entry Point)
├── requirements.txt      # Python Dependencies
├── .env                  # Environment Variables (OLLAMA_API_KEY, etc.)
├── config/
│   ├── config.json       # Global Configuration
│   └── prompts.py        # LLM Prompt Templates
├── data/                 # Knowledge Base Directory (.md, .pdf)
├── libs/                 # Core Libraries
│   ├── config.py         # Configuration Loading
│   ├── db.py             # PostgreSQL Connection Pool Management
│   ├── ollama_client.py  # Ollama Client Wrapper
│   └── utils.py          # General Utility Functions
├── services/              # Business Logic Services
│   ├── chunking.py       # Document Chunking Logic
│   ├── embedding.py      # Vector Generation Service
│   ├── query.py          # Query Processing (Rewrite/HyDE)
│   ├── retrieval.py      # Retrieval and Reranking Logic
│   ├── answer.py         # Answer Generation Service
│   └── storage.py        # Database CRUD Operations
├── chunk/                # Specialized Chunking Implementations
│   └── pdf_chunking.py   # PDF Parsing and Chunking
├── scripts/              # Maintenance and Test Scripts
│   ├── reindex_to_pg.py  # Force Re-index All Files
│   └── verify_parent_child.py # Verify Parent-Child Relationships
├── rag_pg/               # PostgreSQL Deployment Configuration
│   ├── docker-compose.yml # Database Container Configuration
│   └── postgres/         # Custom Postgres Image (including pgvector)
└── Dockerfile            # Application Containerization Configuration
```

## Installation and Startup

### 1. Prerequisites
- Python 3.10+
- [Ollama](https://ollama.ai/) (Installed and running)

### 2. Start PostgreSQL (Recommended via Docker)
Quickly start a database with `pgvector` using the provided configuration:
```bash
cd rag_pg
docker-compose up -d
```

### 3. Environment Configuration
- **Environment Variables**: Create a `.env` file in the root directory
  ```env
  OLLAMA_API_KEY=your_api_key_here
  ```
- **Global Configuration**: Edit `config/config.json` and update `PG_DSN` to match your database connection details.

### 4. Install Dependencies and Start
```bash
pip install -r requirements.txt
# Download required models
ollama pull embeddinggemma
ollama pull gemma4:31b

# Start API Service
uvicorn app:app --reload
```

## API Endpoints

### 1. Question and Answer Interface
- **Endpoint**: `POST /ask`
- **Request**:
  ```json
  {
    "query": "How to install this project?",
    "mode": "rewrite" // Options: "none", "rewrite", "hyde"
  }
  ```
- **Response**: Returns `search_query` (rewritten), `retrieved` (initial results), `reranked` (refined results), and `answer` (final response).

### 2. Data Synchronization Interface
- **Endpoint**: `POST /reindex`
- **Function**: Scans the `data/` directory, calculates hashes, and only updates modified files and chunks in the database.

### 3. File Upload Interface
- **Endpoint**: `POST /upload`
- **Function**: Uploads `.pdf` or `.md` files to the knowledge base directory.

## Core Technical Highlights

- **Incremental Update Mechanism**: Established unique indexes via `(doc_id, chunk_id)` and `text_hash` to avoid redundant and expensive embedding computations.
- **Parent-Child Retrieval**: Uses smaller child chunks for higher precision during retrieval, while providing larger parent chunks during generation to maintain contextual integrity.
- **Query Expansion**: Integrates HyDE and Query Rewrite to address issues where user queries are too brief or semantically drifted.

## License
MIT License