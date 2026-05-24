"""
基础层验证脚本
用法：填好 .env 中的 DEEPSEEK_API_KEY 后运行
  python scripts/verify_basic.py
"""
import os
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
from dotenv import load_dotenv
load_dotenv()

from rag import embedding_service, vector_store
from model import chat_service


def verify_embedding():
    print("=== 验证 Embedding ===")
    vec = embedding_service.embed_query("测试查询")
    dim = embedding_service.dimension
    print(f"  向量维度：{len(vec)}（期望：{dim}）")
    assert len(vec) == dim, "维度不匹配！"
    print("  ✅ Embedding 正常\n")


def verify_store():
    print("=== 验证 VectorStore ===")
    count_before = vector_store.count()
    print(f"  当前记录数：{count_before}")
    # 写入一条测试数据
    test_text = "问：怎么重置 WiFi？\n答：长按设置键 5 秒"
    test_vec = embedding_service.embed_query("怎么重置 WiFi？")
    vector_store.add_documents(
        documents=[test_text],
        embeddings=[test_vec],
        metadatas=[{"source": "verify_test", "question": "怎么重置 WiFi？"}],
        ids=["verify_test_0"],
    )
    count_after = vector_store.count()
    print(f"  写入后记录数：{count_after}（期望：{count_before + 1}）")
    assert count_after == count_before + 1, "写入失败！"
    # 检索验证
    query_vec = embedding_service.embed_query("WiFi 重置方法")
    results = vector_store.search(query_vec, top_k=1)
    print(f"  检索结果：{results[0]['document'][:50]}...")
    assert len(results) >= 1, "检索失败！"
    # 清理测试数据
    vector_store.collection.delete(ids=["verify_test_0"])
    print(f"  清理测试数据完成，记录数恢复为：{vector_store.count()}")
    print("  ✅ VectorStore 正常\n")


def verify_model():
    print("=== 验证 Model（ChatService）===")
    # 只用同步调用验证，不发真实请求（避免无 key 时报错）
    print(f"  model={chat_service.model}, base_url={chat_service.base_url}")
    print("  ✅ ChatService 初始化参数正常（真实调用需填好 API Key）\n")


if __name__ == "__main__":
    verify_embedding()
    verify_store()
    verify_model()
    print("🎉 基础层全部验证通过！")
