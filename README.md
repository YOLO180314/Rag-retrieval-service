# RAG 智能 FAQ 检索服务

基于 RAG（检索增强生成）的智能 FAQ 问答系统。输入自然语言问题，通过向量检索从知识库中找到最匹配的答案，并由 LLM 生成摘要总结。

## 功能

- **向量检索** — ChromaDB 持久化存储，余弦距离排序
- **查询改写** — LLM 将口语化问题改写为规范检索语句，提升召回率
- **AI 摘要** — 对 Top 3 结果自动生成 2-4 句中文总结
- **搜索历史 + 收藏** — localStorage 持久化，支持清空和单条删除
- **暗黑 / 亮色主题** — 一键切换，偏好自动保存

## 快速开始

### 环境要求

- Python 3.11+
- 百炼 DashScope API Key（或其他 OpenAI 兼容 API）

### 安装

```bash
cd rag-retrieval-service
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

### 配置

创建 `.env` 文件：

```env
API_HOST=0.0.0.0
API_PORT=8001
DEEPSEEK_API_KEY=你的_API_Key
DEEPSEEK_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen-plus
EMBEDDING_MODEL=text-embedding-v2
```

### 准备 FAQ 数据

将 Markdown 格式的 FAQ 文档放入 `data/faq/` 目录：

```markdown
**如何重置密码？**
您可以在登录页面点击"忘记密码"，按照提示操作即可重置密码。
```

### 入库 & 启动

```bash
# 1. 解析 FAQ 并写入向量数据库
python main.py --ingest-only

# 2. 后台启动服务
python run_bg.py start

# 3. 打开浏览器
# http://localhost:8001/
```

### 服务管理

```bash
python run_bg.py start      # 启动
python run_bg.py stop       # 停止
python run_bg.py restart    # 重启
python run_bg.py status     # 状态
```

### FAQ 内容更新

修改 `data/faq/` 下的 Markdown 文件后，重新入库即可（upsert 增量更新）：

```bash
# 单文件更新
python scripts/ingest.py --file data/faq/你的文件.md

# 全量更新
python main.py --ingest-only
```

## 架构

```
┌─────────────────────────────────────┐
│           前端 (index.html)          │
│     星空粒子背景 · 毛玻璃卡片         │
├─────────────────────────────────────┤
│          FastAPI (api/)              │
│  /api/search  /api/summarize        │
├─────────────────────────────────────┤
│      检索流水线 (retriever/)         │
│  改写 → 向量化 → 检索               │
├──────────────┬──────────────────────┤
│  LLM (model/) │ 向量 (rag/)         │
│  查询改写+摘要  │  Embedding+ChromaDB │
└──────────────┴──────────────────────┘
```

**依赖方向**：`api → retriever → model / rag`（单向，下层不依赖上层）

## 技术栈

| 层级 | 技术 |
|------|------|
| Web 框架 | FastAPI |
| 向量数据库 | ChromaDB |
| Embedding | 百炼 `text-embedding-v2`（1536 维） |
| LLM | 百炼 `qwen-plus` |
| 前端 | 原生 HTML/CSS/JS（Canvas 粒子背景） |

**未使用 LangChain**，直接使用 OpenAI SDK + ChromaDB 保持轻量。

## 项目结构

```
rag-retrieval-service/
├── main.py                 # 启动入口（API / 仅入库）
├── run_bg.py               # Windows 后台进程管理
├── requirements.txt
├── .env                    # 环境配置
│
├── api/                    # FastAPI 应用层
│   ├── __init__.py
│   └── routes.py
├── retriever/              # 检索编排层
│   ├── pipeline.py
│   └── rewriter.py
├── model/                  # LLM 调用层
│   └── chat.py
├── rag/                    # 向量存储层
│   ├── embedding.py
│   └── store.py
├── scripts/                # 工具脚本
│   ├── ingest.py
│   ├── verify_basic.py
│   └── verify_e2e.py
├── data/faq/               # FAQ 文档（5 个 MD，79 个 Q&A）
└── static/
    └── index.html          # 前端搜索页面
```

## 详细文档

完整的搭建流程、问题排查、UI 优化历程见 [PROJECT_REVIEW.md](./PROJECT_REVIEW.md)。

## License

MIT
