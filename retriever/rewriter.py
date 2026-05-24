"""
查询改写模块：调用 model.ChatService 将用户口语化问题改写为规范检索查询
"""
from model import chat_service


class QueryRewriter:
    """基于 LLM 的查询改写器"""

    def __init__(self, chat_svc=None):
        self.chat = chat_svc or chat_service

    def rewrite(self, question: str) -> str:
        """
        将用户问题改写为更适合向量检索的查询语句
        返回改写后的查询字符串
        """
        prompt = (
            "你是一个智能客服检索系统的查询改写助手。"
            "请将以下用户的口语化问题，改写为一条规范、简洁、保留核心意图的检索查询语句。"
            "只输出改写后的查询语句，不要输出任何解释、序号或标点符号。"
            f"\n\n用户问题：{question}"
        )
        messages = [{"role": "user", "content": prompt}]
        rewritten = self.chat.chat(messages, stream=False)
        # 清理可能的多余换行或引号
        return rewritten.strip().strip('"').strip("'")


# 模块级单例
query_rewriter = QueryRewriter()
