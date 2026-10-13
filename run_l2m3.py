# 运行
import os
import sys
from pathlib import Path

import tiktoken
from langchain.chat_models import ChatOpenAI

from llm_miner import LLMMiner, JournalReader
from llm_miner.config import config


def main():
    if len(sys.argv) != 3:
        sys.exit(
            "用法: python run_l2m3.py 论文路径 出版商\n"
            "例如: python run_l2m3.py data/paper.xml springer"
        )

    paper_path = Path(sys.argv[1]).resolve()
    publisher = sys.argv[2].lower()

    if not paper_path.is_file():
        sys.exit(f"找不到论文: {paper_path}")

    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit("缺少 DeepSeek API Key")

    # 1. 配置 DeepSeek
    model_name = "deepseek-flash"

    config["model_name"] = model_name
    config["simple_model_name"] = model_name
    config["verbose"] = True

    # 兼容 L2M3 使用的 tiktoken
    # 仅用于近似估算 token 数，不是 DeepSeek 官方 tokenizer
    tiktoken.model.MODEL_TO_ENCODING[model_name] = "cl100k_base"

    # 2. 创建 DeepSeek 模型
    llm = ChatOpenAI(
        model_name=model_name,
        temperature=0,
        openai_api_key=api_key,
        openai_api_base="https://api.deepseek.com",
        model_kwargs={
            "extra_body": {
                "thinking": {"type": "disabled"}
            }
        },
    )

    # 3. 读取论文
    print("Reading paper...", flush=True)

    jr = JournalReader.from_file(
        str(paper_path),
        publisher=publisher
    )

    print("Title:", jr.title, flush=True)
    print("DOI:", jr.doi, flush=True)
    print("Elements:", len(jr.elements), flush=True)

    if not jr.elements:
        sys.exit("没有解析到论文内容，停止运行")

    # 4. 创建 L2M3 原始多 Agent 系统
    agent = LLMMiner.from_llm(
        llm=llm,
        simple_llm=llm,
        verbose=True
    )

    # 5. 正式执行全部文献挖掘
    print("Running L2M3...", flush=True)

    agent.run(jr) # LLMMiner继承自LangChain的Chain，调用.run()时会通过LangChain的执行机制进入_call()

    # 6. 保存结果
    output_dir = Path("results")
    output_dir.mkdir(parents=True, exist_ok=True)

    result_file = output_dir / f"{paper_path.stem}_result.json"
    full_file = output_dir / f"{paper_path.stem}_full.json"

    jr.result.to_json(str(result_file))
    jr.to_json(str(full_file))

    print("L2M3 finished!", flush=True)
    print("Result:", result_file)
    print("Full data:", full_file)


if __name__ == "__main__":
    main()

