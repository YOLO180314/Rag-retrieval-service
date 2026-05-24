# RAG 智能 FAQ 检索服务 — 项目回顾文档

> 从零搭建一个完整的 RAG（检索增强生成）FAQ 检索系统，包含后端 API、向量数据库、前端搜索 UI 及 LLM 摘要功能。

---

## 目录

1. [项目概览](#1-项目概览)
2. [技术栈](#2-技术栈)
3. [架构设计](#3-架构设计)
4. [搭建流程](#4-搭建流程)
5. [问题与解决](#5-问题与解决)
6. [前端 UI 优化历程](#6-前端-ui-优化历程)
7. [关键经验总结](#7-关键经验总结)

---

## 1. 项目概览

**定位**：一个面向 FAQ（常见问题）的智能检索服务。用户输入自然语言问题，系统通过向量检索从 FAQ 知识库中找到最匹配的答案，并可选由 LLM 生成摘要。

**数据规模**：5 个 Markdown 文档（覆盖智能门锁、摄像头、网关、售后），共 79 个 Q&A 对。

**核心功能**：
- 自然语言搜索 FAQ 答案（向量相似度检索）
- 查询改写增强召回率（LLM 将口语化问题改写为规范检索语句）
- AI 摘要（对 Top 3 结果自动生成总结）
- 搜索历史 + 收藏功能（localStorage 持久化）
- 暗黑 / 亮色双主题

---

## 2. 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **Web 框架** | FastAPI | 异步 Python Web 框架，自动生成 OpenAPI 文档 |
| **向量数据库** | ChromaDB | 持久化向量存储，余弦距离检索 |
| **Embedding** | OpenAI 兼容 API | 百炼 DashScope `text-embedding-v2`，批量分批处理 |
| **LLM** | OpenAI 兼容 API | `qwen-plus` 模型，用于查询改写和 AI 摘要 |
| **前端** | 原生 HTML/CSS/JS | 单页应用，Canvas 粒子背景，毛玻璃 UI |
| **后台管理** | subprocess + ctypes | Windows 无窗口后台进程管理 |

**明确不使用**：LangChain（保持轻量，直接使用 OpenAI SDK + ChromaDB）。

---

## 3. 架构设计

### 3.1 分层架构

```
┌─────────────────────────────────────┐
│           前端 (index.html)          │  ← 单页应用，搜索 UI
├─────────────────────────────────────┤
│          FastAPI (api/)              │  ← HTTP 路由、Swagger 文档
│  /api/search  /api/summarize        │
├─────────────────────────────────────┤
│      检索流水线 (retriever/)         │  ← 编排层
│  QueryRewriter → Embed → Search     │
├──────────────┬──────────────────────┤
│  LLM (model/) │ 向量 (rag/)         │  ← 原子服务层
│  查询改写+摘要  │  Embedding+ChromaDB │
└──────────────┴──────────────────────┘
```

**依赖方向**：`api → retriever → model / rag`（单向，下层不依赖上层）

### 3.2 目录结构

```
D:/rag-retrieval-service/
├── main.py                 # 启动入口（API / 仅入库两种模式）
├── run_bg.py               # Windows 后台进程管理
├── start.bat               # 批处理启动
├── requirements.txt        # Python 依赖
├── .env                    # 环境配置（API Key、模型等）
│
├── api/                    # FastAPI 应用层
│   ├── __init__.py         # App 创建、Swagger 自定义主题、静态文件托管
│   └── routes.py           # /api/search、/api/summarize、健康检查
│
├── model/                  # LLM 调用层
│   └── chat.py             # ChatService 单例（对话 + 查询改写）
│
├── rag/                    # 向量存储层
│   ├── embedding.py        # Embedding 服务（批量分批向量化）
│   └── store.py            # ChromaDB 持久化向量存储
│
├── retriever/              # 检索编排层
│   ├── rewriter.py         # LLM 查询改写器
│   └── pipeline.py         # 检索流水线（改写 → 向量化 → 检索）
│
├── scripts/                # 工具脚本
│   ├── ingest.py           # FAQ 解析入库
│   ├── verify_basic.py     # 基础组件验证
│   └── verify_e2e.py       # 端到端验证
│
├── data/faq/               # 5 个 FAQ Markdown 文档
├── static/index.html       # 前端搜索页面（~1200 行）
└── chroma_db/              # ChromaDB 持久化数据
```

---

## 4. 搭建流程

### 4.1 环境初始化

```bash
cd D:/rag-retrieval-service
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
```

依赖清单：`fastapi`、`uvicorn`、`chromadb`、`openai`、`python-dotenv`、`pydantic`

### 4.2 配置环境变量

`.env` 文件示例：
```env
API_HOST=0.0.0.0
API_PORT=8001
DEEPSEEK_API_KEY=your_key
DEEPSEEK_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen-plus
EMBEDDING_MODEL=text-embedding-v2
```

### 4.3 数据入库

```bash
# 全量入库：扫描 data/faq/ 下所有 .md 文件
python main.py --ingest-only

# 单文件入库：
python scripts/ingest.py --file data/faq/你的文件.md
```

解析 `data/faq/` 下 Markdown 文件 → 提取 Q&A 对 → Embedding 向量化 → 写入 ChromaDB。

> **增量更新**：`rag/store.py` 使用 `collection.upsert()`（非 `add()`），因此重复 ID 会自动覆盖更新，不会报错。修改 FAQ 文件后直接重新运行入库命令即可。

### 4.4 修改 FAQ 内容

FAQ 文件位于 `data/faq/` 目录，Markdown 格式：

```
**如何重置密码？**
您可以在登录页面点击"忘记密码"，按照提示操作即可重置密码。

**设备离线怎么办？**
首先检查网络连接是否正常...
```

修改后重新入库即可生效：

```bash
# 改了一个文件 → 单文件入库（增量更新，不会影响其他文件）
python scripts/ingest.py --file data/faq/Doc1-X1智能门锁FAQ(1).md

# 改了多个文件 → 全量重新入库
python main.py --ingest-only
```

### 4.5 服务管理

```bash
# 后台启动服务（无窗口运行，日志写入 server.log）
python run_bg.py start

# 查看服务状态
python run_bg.py status

# 重启服务
python run_bg.py restart

# 停止服务
python run_bg.py stop
```

服务地址：`http://localhost:8001/`

**验证服务是否正常**：
```bash
curl http://localhost:8001/health
# 返回：{"status":"ok","collection_count":79}
```

**查看实时日志**（Windows PowerShell）：
```powershell
Get-Content server.log -Wait -Tail 20
```

**如果端口被占用**：修改 `.env` 中的 `API_PORT`，然后重启服务。

### 4.6 前端开发

`static/index.html` 是完整的单页应用，功能包括：
- 搜索框 + 查询改写开关 + Top-K 参数
- 搜索结果卡片（相似度、问题、答案、来源）
- AI 摘要面板
- 搜索历史下拉（localStorage）
- 收藏功能（localStorage）
- Canvas 粒子背景
- 暗黑/亮色主题切换

### 4.7 完整流程：从零到跑起来

以下是从空白环境到服务运行的完整步骤，适合首次部署或换机器后重建。

#### Step 1：进入项目目录

```bash
cd D:/rag-retrieval-service
```

#### Step 2：创建虚拟环境

```bash
python -m venv .venv
```

#### Step 3：激活虚拟环境

```bash
# Windows CMD / PowerShell
.venv\Scripts\activate
```

激活成功后终端提示符前会出现 `(.venv)`。

#### Step 4：安装依赖

```bash
pip install -r requirements.txt
```

#### Step 5：配置环境变量

确保 `.env` 文件存在且配置正确：

```env
API_HOST=0.0.0.0
API_PORT=8001
DEEPSEEK_API_KEY=你的百炼_API_Key
DEEPSEEK_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=qwen-plus
EMBEDDING_MODEL=text-embedding-v2
```

#### Step 6：准备 FAQ 文档

将 FAQ 的 Markdown 文件放入 `data/faq/` 目录。

文件格式要求（两种都支持）：

```
**问题标题？**
答案内容，可以多行。
```

或

```
**问题标题？** 答案内容（单行）
```

#### Step 7：解析入库

```bash
python main.py --ingest-only
```

期望输出：
```
共发现 5 个 FAQ 文件，开始解析...
  ✔ 解析 Doc1-XXX.md：18 个 Q&A 对
  ✔ 解析 Doc2-XXX.md：15 个 Q&A 对
  ...
合计解析 79 个 Q&A 对，开始向量化入库...
  ▶ 向量化 79 条文本（调用 Embedding API）...
  ▶ 写入 ChromaDB...
  ✔ 入库完成，当前总数：79
🎉 全部完成！ChromaDB 中共有 79 条记录。
```

#### Step 8：验证入库结果

```bash
# 快速健康检查
curl http://localhost:8001/health
```

但此时服务还没启动，可以先验证 ChromaDB：

```bash
python -c "from rag import vector_store; print(f'记录数: {vector_store.count()}')"
# 期望输出：记录数: 79
```

#### Step 9：启动 API 服务

```bash
python run_bg.py start
```

期望输出：
```
🚀 正在后台启动 RAG 服务...
✅ 服务已启动 PID: xxxxx → http://0.0.0.0:8001
```

#### Step 10：验证服务运行

```bash
# 检查进程状态
python run_bg.py status

# 健康检查（确认 API 可访问）
curl http://localhost:8001/health
# 返回：{"status":"ok","collection_count":79}
```

#### Step 11：打开前端页面

浏览器打开：**http://localhost:8001/**

你应该看到：
- 星空粒子背景
- 「RAG 智能 FAQ 检索」标题
- 搜索框 + 🔭 欢迎引导
- 点击输入框弹出搜索历史（首次为空）

#### Step 12：测试搜索

输入一个问题，比如"如何重置密码"，点击搜索或按 Enter。

期望结果：
- 返回相似度排序的 FAQ 卡片
- 卡片带入场动画逐张出现
- 顶部显示 AI 摘要卡片
- 底部显示检索耗时

---

**完整命令速查（一次性粘贴）**：

```bash
# === 仅首次（环境搭建）===
cd D:/rag-retrieval-service
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# === 每次需要（入库 + 启动）===
python main.py --ingest-only
python run_bg.py start

# === 验证 ===
curl http://localhost:8001/health
# 浏览器打开 http://localhost:8001/
```

**日常使用**（已搭建好环境后）：
```bash
cd D:/rag-retrieval-service
.venv\Scripts\activate
python run_bg.py start          # 启动
python run_bg.py stop           # 停止
python run_bg.py restart        # 重启
python main.py --ingest-only    # FAQ 变更后重新入库
```

---

## 5. 问题与解决

### 问题 1：模块路径错误导致启动失败

**现象**：`uvicorn.run("api.routes:app")` 报错找不到 app。

**原因**：`app` 实例定义在 `api/__init__.py` 中，不在 `api/routes.py`。

**解决**：改为 `uvicorn.run("api:app")`。

```python
# main.py
uvicorn.run("api:app", host=host, port=port, reload=False)
```

### 问题 2：Windows 进程检测失败

**现象**：`run_bg.py status` 在 Windows 上报错，`os.kill(pid, 0)` 不适用。

**原因**：Windows 没有 POSIX 信号机制，`os.kill(pid, 0)` 无法判断进程存活。

**解决**：使用 `ctypes.windll.kernel32.OpenProcess` 检测进程句柄。

```python
def is_running(pid: int) -> bool:
    import ctypes
    kernel32 = ctypes.windll.kernel32
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    h = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, 0, pid)
    if not h:
        return False
    kernel32.CloseHandle(h)
    return True
```

### 问题 3：搜索历史下拉闪动（最棘手的 bug）

**现象**：点击输入框后，搜索历史下拉框闪一下就消失，需要点第二次才能正常显示。

**根因分析**：这是事件触发顺序导致的问题。

事件触发顺序如下：
```
用户点击输入框
  → mousedown 事件
  → focus 事件 → showDropdown() → 遮罩出现（position:fixed; inset:0; z-index:998）
  → mouseup 事件 → ❌ 此时鼠标下方是遮罩，不再是输入框
  → click 事件被「吞掉」→ 输入框无法收到完整的 click
结果：第一次点击只完成了"显示"，第二次点击才能正常交互
```

**核心矛盾**：`focus` 事件比 `click` 先触发，遮罩在 `click` 完成之前就盖住了输入框。

**最终解决**：给遮罩加 `pointer-events: none`，让点击穿透遮罩。

```css
.history-overlay {
    pointer-events: none;  /* 关键：点击穿透 */
}
```

这么改之后，关闭逻辑完全交给 `document` 级 click 事件：
```javascript
document.addEventListener('click', (e) => {
    if (inputWrapper.contains(e.target)) return;   // 点击输入区 → 不关
    if (historyDropdown.contains(e.target)) return; // 点击浮层 → 不关
    closeHistory();  // 其他区域 → 关闭
});
```

### 问题 4：搜索历史与状态文字重叠

**现象**：搜索历史下拉框和"正在检索…"状态文字区域重叠在一起。

**解决**：
1. 下拉框从 `position:absolute`（嵌入搜索卡片内）改为 `position:fixed`（全屏定位）
2. 设置为最高 z-index 层级（999）
3. 添加遮罩层（z-index: 998）
4. 使用实色背景杜绝透明穿透
5. 把"正在检索…"状态文字移除，查询改写结果放到摘要卡片内，耗时统计放到结果列表底部

---

## 6. 前端 UI 优化历程

以下按实施顺序记录每次 UI 改进。

### 6.1 卡片入场动画

给搜索结果卡片添加从下方淡入的入场动画，逐张延迟播放：

```css
.result-card {
    opacity: 0;
    animation: cardIn .5s ease forwards;
}
@keyframes cardIn {
    from { opacity: 0; transform: translateY(24px); }
    to   { opacity: 1; transform: translateY(0); }
}
```
```javascript
// JS 中设置逐张延迟
cards.forEach((card, i) => {
    card.style.animationDelay = `${i * 0.06}s`;
});
```

### 6.2 搜索按钮加载态

搜索时按钮显示旋转圆环 spinner，替代文字：

```html
<button id="btnSearch">
    <span class="btn-text">搜 索</span>
    <span class="btn-spinner"></span>
</button>
```
```css
.btn-spinner {
    display: none;
    /* 旋转圆环动画 */
}
.btn-search.loading .btn-spinner { display: inline-block; }
```

### 6.3 欢迎引导页

搜索结果为空时显示引导区域："🔭 探索知识宇宙"。

### 6.4 输入框图标

- 左侧 🔍 图标（聚焦时变为主题色）
- 右侧 × 清除按钮（有输入内容时显示）

### 6.5 AI 摘要功能

新增 `POST /api/summarize` 接口，将 Top 3 检索结果发送给 LLM 生成 2-4 句中文摘要。

前端摘要卡片带三点脉冲加载动画，结果以卡片形式展示。

### 6.6 搜索历史下拉重构

这是改动最大的部分，经历了多次迭代：

| 版本 | 方案 | 问题 |
|------|------|------|
| v1 | `position:absolute` 嵌入搜索卡片 | 与状态文字重叠 |
| v2 | 降低透明度到接近不透 | 用户觉得太厚重 |
| v3 | `position:fixed` + 实色背景 + z-index 最高层 | 终于不重叠了 |
| v4 | 加遮罩 + 去掉 blurred 模糊 | 用户要求的效果 |
| v5 | 先定位后显示（防闪动） | 还会闪一下 |
| v6 | **`pointer-events: none`** | ✅ 彻底解决 |

**最终方案要点**：
- 下拉框 `position:fixed`，`z-index: 999`
- 遮罩 `position:fixed; inset:0`，`z-index: 998`，`background: rgba(0,0,0,0.2)`
- 遮罩 `pointer-events: none` → 点击穿透
- 先计算位置，再同时显示遮罩和浮层

### 6.7 状态信息重组

- 去掉搜索区域的"正在检索…"动态文字
- 查询改写结果移到 AI 摘要卡片内展示
- 检索耗时显示在结果列表底部

---

## 7. 关键经验总结

### 架构设计
- **分层单向依赖**让代码清晰：`api → retriever → model/rag`，每层职责单一
- **配置集中管理**：`.env` 文件统一管理所有密钥和参数，模块用独立前缀避免冲突
- **先确认后编码**：列出目录结构和任务清单，确认后再动手写代码，避免返工
- **验证标注格式**：检查结果用 `IS_PASS: YES / NO` 标注，一目了然

### 前端开发
- **`focus` vs `click` 事件顺序**：`focus` 先于 `click` 触发，如果在 `focus` 中改变 DOM（比如显示遮罩），可能干扰 `click` 事件完成
- **`pointer-events: none`** 是解决遮罩层干扰交互的神器——让遮罩只做视觉遮挡，不做事件拦截
- **`position:fixed` + 高 z-index**：要做真正浮在最上层的元素，必须脱离文档流
- **先定位后显示**：避免元素先出现在错误位置再跳过去的闪动

### 后端开发
- **Windows 兼容性**：`os.kill()` 等 POSIX 方法在 Windows 不可用，需用 `ctypes` 调用 Win32 API
- **模块导入路径**：FastAPI 中 `uvicorn.run("module:var")` 的 `module` 是 Python 导入路径，不是文件路径
- **ChromaDB 外部传入向量**：不使用内置 embedding function，由自己的 Embedding 服务控制向量化过程

### 协作习惯
- 工作区整洁：及时清理临时文件、构建产物
- 每个实质改动后写入工作记忆，便于跨会话追溯
- bug 修复遵循「分析根因 → 确认理解 → 最小改动」原则

---

*文档生成时间：2026-05-24*
*项目路径：D:/rag-retrieval-service/*
