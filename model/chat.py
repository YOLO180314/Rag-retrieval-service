import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class ChatService:
    """文本生成服务（兼容 OpenAI SDK，支持百炼/DeepSeek/OpenAI 等）"""

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.openai.com/v1")
        self.model = model or os.getenv("MODEL_NAME", "qwen-plus")
        self.temperature = temperature if temperature is not None else float(os.getenv("MODEL_TEMPERATURE", "0.7"))
        self.max_tokens = max_tokens or int(os.getenv("MODEL_MAX_TOKENS", "1024"))

        if not self.api_key or self.api_key == "your_deepseek_api_key_here":
            raise ValueError("DEEPSEEK_API_KEY 未配置，请在 .env 中填写真实密钥")

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def chat(self, messages: list, stream: bool = False):
        """同步对话，返回完整文本；stream=True 时返回 Generator"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=stream,
            )
            if stream:
                return self._stream_iterator(response)
            else:
                return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"模型调用失败: {e}") from e

    def _stream_iterator(self, response):
        for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def rewrite_query(self, question: str, prompt_template: str = None) -> str:
        """查询改写：将用户问题改写为更适合向量检索的版本"""
        if prompt_template is None:
            prompt_template = (
                "请将以下用户问题改写为更规范、更完整的检索查询语句，"
                "保留关键信息，去掉口语化表达，只输出改写后的结果，不要输出任何解释：\n\n{question}"
            )
        messages = [{"role": "user", "content": prompt_template.format(question=question)}]
        return self.chat(messages, stream=False)


# 模块级单例
chat_service = ChatService()
