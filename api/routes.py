"""
FastAPI 路由：对外暴露 HTTP 检索接口
"""
from typing import Optional, List, Dict
from fastapi import APIRouter
from pydantic import BaseModel, Field
from dotenv import load_dotenv
load_dotenv()

from retriever import retrieval_pipeline

router = APIRouter()


class SearchRequest(BaseModel):
    question: str
    enable_rewrite: bool = True
    top_k: Optional[int] = None


class HealthResponse(BaseModel):
    status: str
    collection_count: int


class SummarizeRequest(BaseModel):
    query: str = Field(..., description="用户原始问题")
    results: List[Dict] = Field(..., description="检索结果列表，每项含 question/answer/score")


class SummarizeResponse(BaseModel):
    summary: str
    result_count: int


@router.post("/search")
def search(req: SearchRequest):
    """
    检索接口
    - question: 用户原始问题
    - enable_rewrite: 是否启用 LLM 查询改写（默认 True）
    - top_k: 返回结果数量（默认读 .env 的 RETRIEVER_TOP_K）
    """
    result = retrieval_pipeline.search(
        question=req.question,
        enable_rewrite=req.enable_rewrite,
        top_k=req.top_k,
    )
    return result


@router.get("/health", response_model=HealthResponse)
def health():
    """健康检查"""
    from rag import vector_store
    return {
        "status": "ok",
        "collection_count": vector_store.count(),
    }


@router.post("/summarize", response_model=SummarizeResponse)
def summarize(req: SummarizeRequest):
    """
    AI 摘要接口
    根据用户问题和检索结果，用 LLM 生成一份简洁的摘要总结。
    """
    from model import chat_service

    # 拼接 Q&A 上下文
    qa_text = "\n\n".join([
        f"【问题{r['idx']}】{r.get('question','')}\n【答案{r['idx']}】{r.get('answer','')}"
        for r in req.results
    ])

    prompt = (
        "你是一个知识库助手。请根据以下搜索结果，用中文生成一段简洁的摘要，"
        "帮助用户快速了解核心信息。\n\n"
        f"用户问题：{req.query}\n\n"
        f"搜索结果（共{len(req.results)}条）：\n{qa_text}\n\n"
        "请用 2-4 句话总结关键信息。如果结果中信息不足，请如实说明。"
        "直接输出摘要内容，不要加任何前缀标签。"
    )

    messages = [{"role": "user", "content": prompt}]
    summary = chat_service.chat(messages, stream=False)

    return SummarizeResponse(
        summary=summary.strip(),
        result_count=len(req.results),
    )
