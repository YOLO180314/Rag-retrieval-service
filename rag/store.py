import os
import uuid
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

try:
    import chromadb
except ImportError:
    raise ImportError("请先安装 chromadb：pip install chromadb")


class VectorStore:
    """ChromaDB 向量存储，外部传入向量（由 embedding_service 生成）"""

    def __init__(
        self,
        persist_dir: str = None,
        collection_name: str = None,
    ):
        self.persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self.collection_name = collection_name or os.getenv("COLLECTION_NAME", "faq_collection")

        self.client = chromadb.PersistentClient(path=self.persist_dir)
        # 不传 embedding_function，向量由外部生成后传入
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
        )

    def add_documents(
        self,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: Optional[list[dict]] = None,
        ids: Optional[list[str]] = None,
    ) -> list[str]:
        """写入文档（向量由外部传入）"""
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        if metadatas is None:
            metadatas = [{} for _ in documents]

        # upsert：新 ID 插入，已有 ID 覆盖更新，支持增量入库
        self.collection.upsert(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        return ids

    def search(
        self,
        query_embedding: list[float],
        top_k: int = None,
        score_threshold: float = None,
    ) -> list[dict]:
        """向量检索（向量由外部传入）"""
        if top_k is None:
            top_k = int(os.getenv("RETRIEVER_TOP_K", "3"))
        if score_threshold is None:
            score_threshold = float(os.getenv("RETRIEVER_SCORE_THRESHOLD", "0.0"))

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        output = []
        for i, doc in enumerate(results["documents"][0]):
            distance = results["distances"][0][i]
            # score_threshold > 0 时按阈值过滤（只保留距离 ≤ 阈值的），0 表示不过滤
            if score_threshold > 0 and distance > score_threshold:
                continue
            output.append({
                "document": doc,
                "metadata": results["metadatas"][0][i],
                "distance": round(distance, 4),
                "id": results["ids"][0][i],
            })
        return output

    def count(self) -> int:
        return self.collection.count()

    def reset(self):
        """清空当前 collection（仅开发环境使用）"""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
        )


# 模块级单例
vector_store = VectorStore()
