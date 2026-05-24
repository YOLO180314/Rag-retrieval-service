import os
from dotenv import load_dotenv

load_dotenv()

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("请先安装 openai：pip install openai")


class EmbeddingService:
    """OpenAI 兼容 Embedding 服务（百炼 DashScope / OpenAI 原生均可）"""

    def __init__(
        self,
        model_name: str = None,
        api_key: str = None,
        base_url: str = None,
    ):
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "text-embedding-v2")
        self._api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self._base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.openai.com/v1")
        self._client = None
        self._dimension = None

    @property
    def client(self):
        if self._client is None:
            if not self._api_key:
                raise ValueError(
                    "未找到 API Key，请在 .env 中设置 DEEPSEEK_API_KEY=你的key"
                )
            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
            )
        return self._client

    @property
    def dimension(self) -> int:
        """向量维度（首次调用 embed 后确定）"""
        if self._dimension is None:
            # 触发一次 embed 来确定维度
            test_embedding = self.embed(["test"])
            self._dimension = len(test_embedding[0])
        return self._dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        批量向量化，返回 list[list[float]]
        自动分批（百炼 API 限制每批 ≤ 25 条）
        """
        batch_size = 25
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self.client.embeddings.create(
                model=self.model_name,
                input=batch,
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            if self._dimension is None and batch_embeddings:
                self._dimension = len(batch_embeddings[0])
        return all_embeddings

    def embed_query(self, text: str) -> list[float]:
        """单条查询向量化"""
        return self.embed([text])[0]


# 模块级单例
embedding_service = EmbeddingService()
