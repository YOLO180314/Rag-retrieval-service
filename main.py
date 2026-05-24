"""
启动入口
用法：
  python main.py                  # 以 uvicorn 启动 API 服务（默认 0.0.0.0:8000）
  python main.py --ingest-only   # 只执行 FAQ 入库，不启动服务
"""
import sys
import os
import argparse
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)


def start_api():
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8001"))
    print(f"🚀 启动 RAG 检索服务：http://{host}:{port}")
    print(f"   API 文档：http://localhost:{port}/docs")
    uvicorn.run("api:app", host=host, port=port, reload=False)


def ingest_only():
    from scripts.ingest import main as ingest_main
    # 重新以脚本方式调用入库逻辑
    from rag import vector_store
    print(f"📥 开始 FAQ 入库流程...")
    from scripts.ingest import parse_faq_file, ingest_qa_pairs
    import glob
    faq_dir = os.path.join(os.path.dirname(__file__), "data", "faq")
    md_files = glob.glob(os.path.join(faq_dir, "*.md"))
    if not md_files:
        print("⚠ data/faq/ 目录下没有 .md 文件")
        return
    all_qa = []
    for fp in md_files:
        all_qa.extend(parse_faq_file(fp))
    print(f"合计 {len(all_qa)} 个 Q&A 对，开始入库...")
    ingest_qa_pairs(all_qa)
    print(f"✅ 入库完成！ChromaDB 共有 {vector_store.count()} 条记录。")


if __name__ == "__main__":
    import os
    parser = argparse.ArgumentParser(description="RAG 检索服务启动入口")
    parser.add_argument("--ingest-only", action="store_true", help="只执行 FAQ 入库，不启动 API 服务")
    args = parser.parse_args()

    if args.ingest_only:
        ingest_only()
    else:
        start_api()
