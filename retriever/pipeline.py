"""
检索编排层：组合查询改写（rewriter）与向量检索（rag）
"""
import os
from dotenv import load_dotenv

load_dotenv()

from model import chat_service
from rag import embedding_service, vector_store
from .rewriter import query_rewriter


class RetrievalPipeline:
    """端到端检索流水线"""

    def __init__(self, top_k: int = None, enable_rewrite_default: bool = True):
        self.top_k = top_k or int(os.getenv("RETRIEVER_TOP_K", "3"))
        self.enable_rewrite_default = enable_rewrite_default
        self.rewriter = query_rewriter
        self.store = vector_store

    def search(
        self,
        question: str,
        enable_rewrite: bool = None,
        top_k: int = None,
    ) -> dict:
        """
        执行一次完整检索，返回详细结果字典
        enable_rewrite: 是否启用查询改写，None 时使用默认值
        """
        if enable_rewrite is None:
            enable_rewrite = self.enable_rewrite_default

        result = {
            "original_question": question,
            "enable_rewrite": enable_rewrite,
            "rewritten_query": None,
            "results": [],
        }

        # Step1：查询改写（可选）
        query_for_search = question
        if enable_rewrite:
            rewritten = self.rewriter.rewrite(question)
            result["rewritten_query"] = rewritten
            query_for_search = rewritten

        # Step2：向量化查询文本
        query_embedding = embedding_service.embed_query(query_for_search)

        # Step3：向量检索
        hits = self.store.search(query_embedding, top_k=top_k or self.top_k)

        # 格式化返回结果（ChromaDB 返回的是余弦距离，转成相似度）
        result["results"] = [
            {
                "score": round(1 - h["distance"], 4),
                "distance": round(h["distance"], 4),
                "document": h["document"],
                "metadata": h["metadata"],
            }
            for h in hits
        ]
        return result


# 模块级单例
retrieval_pipeline = RetrievalPipeline()
