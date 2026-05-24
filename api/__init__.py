import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from dotenv import load_dotenv

load_dotenv()

from .routes import router

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# ── Ins 黑白灰风格 Swagger 主题 CSS ──
SWAGGER_CSS = """
<style>
  /* ===== 全局 ===== */
  * { font-family: -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important; }
  body { background: #fafafa !important; }

  /* ===== 顶部栏 ===== */
  .topbar { background: #000 !important; border-bottom: 1px solid #e0e0e0 !important; }
  .topbar .download-url-wrapper { display: none !important; }
  .topbar .link { color: #fff !important; }

  /* ===== 标题区 ===== */
  .swagger-ui .info { margin: 24px 0 !important; padding: 20px 24px !important; background: #fff !important; border: 1px solid #e0e0e0 !important; border-radius: 12px !important; }
  .swagger-ui .info .title { color: #111 !important; font-weight: 700 !important; font-size: 22px !important; }
  .swagger-ui .info .title small { background: #111 !important; border-radius: 6px !important; font-size: 11px !important; padding: 2px 8px !important; }
  .swagger-ui .info p, .swagger-ui .info a { color: #555 !important; }

  /* ===== 服务器选择 ===== */
  .swagger-ui .scheme-container { background: #fff !important; border: 1px solid #e0e0e0 !important; border-radius: 12px !important; padding: 16px 24px !important; margin: 16px 0 !important; box-shadow: none !important; }
  .swagger-ui .scheme-container label { color: #333 !important; font-weight: 500 !important; }
  select { border: 1px solid #ccc !important; border-radius: 8px !important; padding: 6px 12px !important; background: #fff !important; color: #111 !important; }

  /* ===== 操作块（每个接口卡片） ===== */
  .swagger-ui .opblock { border-radius: 12px !important; border: 1px solid #e0e0e0 !important; margin: 12px 0 !important; box-shadow: none !important; overflow: hidden !important; }
  .swagger-ui .opblock-summary { padding: 14px 20px !important; }
  .swagger-ui .opblock-summary-method { border-radius: 6px !important; font-weight: 600 !important; font-size: 12px !important; padding: 4px 10px !important; min-width: 56px !important; text-align: center !important; }

  /* POST - 黑底白字 */
  .swagger-ui .opblock-post { background: #fff !important; border-color: #111 !important; }
  .swagger-ui .opblock-post .opblock-summary-method { background: #111 !important; color: #fff !important; }
  .swagger-ui .opblock-post .opblock-summary-path { color: #111 !important; font-weight: 500 !important; }

  /* GET - 灰底黑字 */
  .swagger-ui .opblock-get { background: #fff !important; border-color: #555 !important; }
  .swagger-ui .opblock-get .opblock-summary-method { background: #333 !important; color: #fff !important; }
  .swagger-ui .opblock-get .opblock-summary-path { color: #111 !important; font-weight: 500 !important; }

  /* ===== 展开区域 ===== */
  .swagger-ui .opblock-body { background: #fff !important; padding: 0 20px 16px !important; }
  .swagger-ui .opblock-section { padding: 12px 0 !important; }
  .swagger-ui .opblock-section-header { background: #f5f5f5 !important; border: none !important; border-radius: 8px !important; padding: 10px 16px !important; }
  .swagger-ui .opblock-section-header h4 { color: #111 !important; font-weight: 600 !important; }

  /* ===== 按钮 ===== */
  .swagger-ui .btn { border-radius: 8px !important; font-weight: 500 !important; border: none !important; }
  .swagger-ui .btn.execute { background: #111 !important; color: #fff !important; padding: 8px 20px !important; }
  .swagger-ui .btn.execute:hover { background: #333 !important; }
  .swagger-ui .btn.cancel { background: #e0e0e0 !important; color: #111 !important; }
  .swagger-ui .btn.authorize { background: #111 !important; color: #fff !important; border: none !important; }
  .swagger-ui .btn.authorize:hover { background: #333 !important; }
  .swagger-ui .btn.close-modal { background: #e0e0e0 !important; color: #111 !important; }

  /* ===== 输入框 & 表格 ===== */
  .swagger-ui input[type=text], .swagger-ui textarea, .swagger-ui select {
    border: 1px solid #ddd !important; border-radius: 8px !important; padding: 8px 12px !important; background: #fafafa !important; color: #111 !important;
  }
  .swagger-ui input[type=text]:focus, .swagger-ui textarea:focus { border-color: #111 !important; outline: none !important; }
  .swagger-ui table { border-radius: 8px !important; overflow: hidden !important; }
  .swagger-ui table thead tr th { background: #111 !important; color: #fff !important; font-weight: 500 !important; border: none !important; }
  .swagger-ui table tbody tr td { border-bottom: 1px solid #eee !important; color: #333 !important; }
  .swagger-ui table tbody tr:nth-child(odd) { background: #fafafa !important; }

  /* ===== Model / Schema 区域 ===== */
  .swagger-ui .model-box { background: #f5f5f5 !important; border: 1px solid #e0e0e0 !important; border-radius: 8px !important; }
  .swagger-ui .model-title { color: #111 !important; font-weight: 600 !important; }
  .swagger-ui .model { color: #333 !important; }
  .swagger-ui .prop-type { color: #888 !important; }
  .swagger-ui .prop-name { color: #111 !important; font-weight: 500 !important; }

  /* ===== 响应区域 ===== */
  .swagger-ui .responses-wrapper { border-top: 1px solid #eee !important; padding-top: 12px !important; }
  .swagger-ui .response-col_status { font-weight: 600 !important; }
  .swagger-ui .response-undocumented { color: #999 !important; }

  /* ===== 滚动条 ===== */
  ::-webkit-scrollbar { width: 6px !important; }
  ::-webkit-scrollbar-track { background: #fafafa !important; }
  ::-webkit-scrollbar-thumb { background: #ccc !important; border-radius: 3px !important; }
  ::-webkit-scrollbar-thumb:hover { background: #999 !important; }

  /* ===== 底部 ===== */
  .swagger-ui .info .license { color: #999 !important; }
  .swagger-ui .info .license a { color: #111 !important; font-weight: 500 !important; }

  /* ===== 模态框 ===== */
  .swagger-ui .dialog-ux { background: rgba(0,0,0,0.5) !important; }
  .swagger-ui .dialog-ux .modal { border-radius: 16px !important; border: none !important; box-shadow: 0 20px 60px rgba(0,0,0,0.15) !important; }
  .swagger-ui .dialog-ux .modal .modal-header { background: #111 !important; color: #fff !important; border-radius: 16px 16px 0 0 !important; }
  .swagger-ui .dialog-ux .modal .modal-header .close-modal { color: #fff !important; }
</style>
"""

# ── 自定义 Swagger HTML（注入 CSS） ──
SWAGGER_HTML = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>RAG 检索服务 - API 文档</title>
  <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"/>
  {SWAGGER_CSS}
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    SwaggerUIBundle({{
      url: '/openapi.json',
      dom_id: '#swagger-ui',
      deepLinking: true,
      presets: [SwaggerUIBundle.presets.apis],
    }});
  </script>
</body>
</html>
"""


# ── FastAPI App ──
app = FastAPI(
    title="RAG 检索增强服务",
    description="""
## 🔍 服务说明

基于 **ChromaDB + 大模型** 的智能 FAQ 检索服务。

### 核心接口
- **`POST /api/search`** — 检索 FAQ，支持 LLM 查询改写
- **`GET /api/health`** — 健康检查，返回向量库条目数

### 使用流程
1. 准备 FAQ 文档（Markdown 格式），放入 `data/faq/` 目录
2. 执行 `python main.py --ingest-only` 入库
3. 启动服务 `python main.py`，访问 `http://localhost:8001/docs`
""",
    version="1.0.0",
    contact={"name": "RAG Service", "url": "http://localhost:8001"},
    openapi_version="3.1.0",
)


app.include_router(router, prefix="/api")

# 托管静态文件
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", tags=["页面"], summary="搜索页面", description="返回前端搜索页面（HTML）")
def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/docs", tags=["文档"], summary="Swagger API 文档", description="返回自定义样式的 Swagger UI 文档页面")
def docs():
    return HTMLResponse(content=SWAGGER_HTML, media_type="text/html")


@app.get("/health", tags=["系统"], summary="健康检查", description="返回服务状态和向量库中文档数量")
def health():
    from rag import vector_store
    return {"status": "ok", "collection_count": vector_store.count()}
