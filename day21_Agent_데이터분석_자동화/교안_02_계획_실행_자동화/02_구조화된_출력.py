"""교안 02-2: 에이전트의 자유 문장을 정해진 틀로 바꾸기

핵심 목표
    에이전트 답변은 매번 문장이 달라 그대로는 표에 쌓을 수 없다.
    with_structured_output 으로 정해진 틀에 맞춰 받아 표·JSON 으로 적재한다.

순서
    1) 에이전트가 평소처럼 문장으로 답한다
    2) 그 문장을 틀(AnalysisResult)로 바꾼다
    3) 딕셔너리를 모아 표로 만들고 JSON 으로 남긴다

실행: 이 파일이 있는 폴더에서  uv run 02_구조화된_출력.py

OPENAI_API_KEY 가 필요합니다(일차 폴더의 .env).
"""

import asyncio
import sys
from pathlib import Path

import pandas as pd
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

sys.path.append(str(Path(__file__).resolve().parent.parent))   # 일차 폴더의 utils.py 를 쓴다

from utils import chinook_db_path, load_api_key, print_trajectory, quiet_stdio_logs


quiet_stdio_logs()

DAY_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = DAY_DIR / "data"
OUTPUT_DIR = DAY_DIR / "output"
load_api_key(DAY_DIR)

DB_PATH = chinook_db_path(DATA_DIR)
SQLITE = {"command": "uvx",
          "args": ["--with", "mcp==1.9.4", "--from", "mcp-server-sqlite",
                   "mcp-server-sqlite", "--db-path", str(DB_PATH)],
          "transport": "stdio"}

SYSTEM = ("너는 데이터 분석 비서다. 표의 조회·집계는 read_query 로 SQL 을 실행해 구한다. "
          "숫자를 암산하거나 지어내지 않는다. "
          "표나 열 이름이 확실하지 않으면 list_tables 와 describe_table 로 먼저 확인한다.")

# 정형화는 '수치 하나로 답이 나오는 질문' 일 때 잘 맞는다.
QUESTIONS = [
    "국가별 매출 합계에서 가장 매출이 큰 국가와 그 합계를 알려줘.",
    "직원별 담당 고객 매출 합계에서 1위 직원과 그 합계를 알려줘.",
]


class AnalysisResult(BaseModel):
    """분석 답변을 담는 정해진 틀. 지표 이름·핵심 수치·한 문장 해석."""
    # 필드 설명은 '이 칸에 무엇이 들어가는가' 를 짧은 명사구로 적는다.
    # "~하라", "~쓰지 마라" 처럼 긴 지시문으로 쓰면 모델이 그 문장을 값으로 베껴 넣는다.
    metric: str = Field(description="집계 대상과 방법이 드러나는 한국어 지표 이름. 예: 매출 1위 국가의 매출 합계")
    value: float = Field(description="핵심 수치 하나. 단위 없는 숫자")
    interpretation: str = Field(description="그 수치를 설명하는 한국어 한 문장")


async def main():
    print("DB 서버를 띄우는 중입니다(첫 실행은 오래 걸립니다)...")
    tools = await MultiServerMCPClient({"db": SQLITE}).get_tools()
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60)
    agent = create_agent(
        model, tools, system_prompt=SYSTEM,
        middleware=[ModelCallLimitMiddleware(run_limit=12, exit_behavior="end")],
    )
    # 틀에 맞춰 받는 쪽은 도구 없이 한 번만 부른다. 그래서 결과가 일정하다.
    structurer = model.with_structured_output(AnalysisResult)

    rows = []
    for question in QUESTIONS:
        print(f"\n=== 질문: {question} ===")

        # 1단계: 에이전트가 평소처럼 문장으로 답한다.
        result = await agent.ainvoke({"messages": question})
        print_trajectory(result)
        answer_text = result["messages"][-1].text

        # 2단계: 그 문장을 틀로 바꾼다. 질문과 답변을 함께 넣는다.
        # 답변만 주면 지표 이름이 '매출' 처럼 뭉뚱그려진다. 무엇을 집계한 값인지는 질문에 있다.
        # 답변을 함께 주는 것이 중요하다. 그래야 이 호출이 새로 답하지 않고 옮겨 담기만 한다.
        info = structurer.invoke(f"질문: {question}\n답변: {answer_text}")
        print(f"\n[틀에 담은 결과] {info.metric} = {info.value} ({type(info.value).__name__})")
        print(f"                  {info.interpretation}")
        rows.append(info.model_dump())

    # 3단계: 딕셔너리를 모으면 표가 되고, 표는 JSON 으로 남는다.
    print("\n=== 표로 쌓기 ===")
    metrics_df = pd.DataFrame(rows)
    print(metrics_df)
    print("\n자료형:")
    print(metrics_df.dtypes)      # value 가 문자열이 아니라 숫자(float)인지 확인한다

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics_path = OUTPUT_DIR / "metrics.json"
    # orient='records' 는 '행 하나 = 객체 하나', force_ascii=False 는 한글을 그대로 쓰기 위한 옵션
    metrics_df.to_json(metrics_path, orient="records", force_ascii=False)
    print("\n지표 저장:", metrics_path)
    print(metrics_path.read_text(encoding="utf-8")[:300])

    print("\n[요점] 문장은 실행할 때마다 달라지지만, 틀에 담으면 열 이름과 자료형이 고정된다.")
    print("       그래야 표에 쌓이고, 대시보드나 다음 단계가 그 값을 그대로 쓸 수 있다.")


if __name__ == "__main__":
    asyncio.run(main())
