"""
FAQ 文档解析与入库脚本
用法：
  python scripts/ingest.py              # 扫描 data/faq 目录，解析所有 .md 文件并入库
  python scripts/ingest.py --file path  # 入库单个文件
"""
import os
import re
import argparse
import sys

# 确保项目根目录在 sys.path 中，支持从任意目录启动
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

from rag import embedding_service, vector_store


def parse_faq_file(file_path: str) -> list[dict]:
    """
    解析单个 FAQ MD 文件，返回 [{"question": ..., "answer": ..., "source": ...}, ...]
    支持两种格式：
      格式A（单行）：**问题？** 答案文本
      格式B（多行）：**问题？**\n答案文本（可多行，直到下一个 **问题？**）
    """
    with open(file_path, "r", encoding="utf-8-sig") as f:
        lines = [line.rstrip("\n") for line in f]

    qa_pairs = []
    current_q = None
    current_a_lines = []

    def flush():
        """将当前积累的 Q&A 写入结果列表"""
        nonlocal current_q, current_a_lines
        if current_q is not None:
            answer = "\n".join(current_a_lines).strip()
            if answer:  # 只保留有答案的条目
                qa_pairs.append({
                    "question": current_q,
                    "answer": answer,
                    "source": os.path.basename(file_path),
                })
        current_q = None
        current_a_lines = []

    for line in lines:
        # 匹配 **问题？** 独占一行的格式（支持中英文问号）
        q_match = re.match(r"^\*\*(.+?\？)\*\*\s*$", line) or \
                  re.match(r"^\*\*(.+?\?)\*\*\s*$", line)
        if q_match:
            # 遇到新题目，先保存上一题
            flush()
            current_q = q_match.group(1).strip()
            current_a_lines = []
        else:
            # 普通行：属于当前题目的答案
            if current_q is not None:
                current_a_lines.append(line)

    # 文件结束，flush 最后一题
    flush()

    print(f"  ✔ 解析 {os.path.basename(file_path)}：{len(qa_pairs)} 个 Q&A 对")
    return qa_pairs


def ingest_qa_pairs(qa_pairs: list[dict]):
    """将 Q&A 对向量化后写入 ChromaDB"""
    if not qa_pairs:
        print("  ⚠ 无有效 Q&A 对，跳过入库")
        return

    texts = [f"问：{item['question']}\n答：{item['answer']}" for item in qa_pairs]
    metadatas = [
        {"source": item["source"], "question": item["question"], "answer": item["answer"]}
        for item in qa_pairs
    ]
    ids = [f"{item['source']}_{i}" for i, item in enumerate(qa_pairs)]

    print(f"  ▶ 向量化 {len(texts)} 条文本（调用 Embedding API）...")
    embeddings = embedding_service.embed(texts)
    print(f"  ▶ 写入 ChromaDB...")
    vector_store.add_documents(
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )
    print(f"  ✔ 入库完成，当前总数：{vector_store.count()}")


def main():
    parser = argparse.ArgumentParser(description="FAQ 文档解析与向量入库")
    parser.add_argument("--file", type=str, default=None, help="指定单个 MD 文件路径，不指定则扫描 data/faq 目录")
    args = parser.parse_args()

    faq_dir = os.path.join(PROJECT_ROOT, "data", "faq")
    os.makedirs(faq_dir, exist_ok=True)

    if args.file:
        files = [args.file]
    else:
        files = [
            os.path.join(faq_dir, f)
            for f in os.listdir(faq_dir)
            if f.endswith(".md")
        ]
        if not files:
            print(f"⚠ data/faq/ 目录下没有 .md 文件，请将 FAQ 文档放入该目录后重试。")
            return

    print(f"共发现 {len(files)} 个 FAQ 文件，开始解析...")
    all_qa = []
    for fp in files:
        qa_pairs = parse_faq_file(fp)
        all_qa.extend(qa_pairs)

    print(f"\n合计解析 {len(all_qa)} 个 Q&A 对，开始向量化入库...\n")
    ingest_qa_pairs(all_qa)
    print(f"\n🎉 全部完成！ChromaDB 中共有 {vector_store.count()} 条记录。")


if __name__ == "__main__":
    main()
