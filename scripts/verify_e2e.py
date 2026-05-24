"""
端到端验证脚本
填好 .env 的 DEEPSEEK_API_KEY 后运行：
  python scripts/verify_e2e.py
"""
import os
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
from dotenv import load_dotenv
load_dotenv()

from rag import embedding_service, vector_store
from retriever import retrieval_pipeline


def verify_e2e():
    print("=== 端到端验证开始 ===\n")

    # 1. 检查 ChromaDB 是否有数据
    count = vector_store.count()
    print(f"[1] ChromaDB 记录数：{count}")
    if count == 0:
        print("  ⚠ 数据库为空，请先运行：python main.py --ingest-only")
        return

    # 2. 测试直接检索（不改写）
    print("\n[2] 测试直接检索（enable_rewrite=False）...")
    result_no_rewrite = retrieval_pipeline.search(
        question="怎么重置 WiFi",
        enable_rewrite=False,
    )
    print(f"  原始问题：{result_no_rewrite['original_question']}")
    print(f"  召回结果数：{len(result_no_rewrite['results'])}")
    if result_no_rewrite["results"]:
        top = result_no_rewrite["results"][0]
        print(f"  Top1 相似度：{top['score']}")
        print(f"  Top1 内容：{top['document'][:80]}...")

    # 3. 测试改写 + 检索
    print("\n[3] 测试改写检索（enable_rewrite=True）...")
    result_rewrite = retrieval_pipeline.search(
        question="忘了怎么连 WiFi 了",
        enable_rewrite=True,
    )
    print(f"  原始问题：{result_rewrite['original_question']}")
    print(f"  改写后查询：{result_rewrite.get('rewritten_query', '(未改写)')}")
    print(f"  召回结果数：{len(result_rewrite['results'])}")
    if result_rewrite["results"]:
        top = result_rewrite["results"][0]
        print(f"  Top1 相似度：{top['score']}")

    # 4. 对比改写前后的 Top1 相似度
    print("\n[4] 改写效果对比...")
    score_no_rewrite = result_no_rewrite["results"][0]["score"] if result_no_rewrite["results"] else 0
    score_rewrite = result_rewrite["results"][0]["score"] if result_rewrite["results"] else 0
    print(f"  直接检索 Top1 相似度：{score_no_rewrite}")
    print(f"  改写检索 Top1 相似度：{score_rewrite}")
    if score_rewrite > score_no_rewrite:
        print("  ✅ 改写后相似度提升！")
    else:
        print("  ⚠ 改写后相似度未提升，可优化 prompt")

    print("\n🎉 端到端验证完成！")


if __name__ == "__main__":
    verify_e2e()
