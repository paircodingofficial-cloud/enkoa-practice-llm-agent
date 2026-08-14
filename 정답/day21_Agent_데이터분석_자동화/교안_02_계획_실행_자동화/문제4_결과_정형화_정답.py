"""📝 과제 문제 4 정답: 자유 문장으로 온 답을 정해진 틀에 담아 JSON 으로 남기기

준비물: OPENAI_API_KEY(일차 폴더 .env) · npx(Node.js) · uvx(uv)
실행: 이 파일이 있는 폴더에서  uv run 문제4_결과_정형화_정답.py
"""

import asyncio
import json
import sys
from pathlib import Path

# 실습 폴더의 과제 파일들이 함께 쓰는 공통.py 를 그대로 씁니다
sys.path.append(str(Path(__file__).resolve().parents[3] / "day21_Agent_데이터분석_자동화" / "교안_02_계획_실행_자동화" / "과제"))

import pandas as pd
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain_core.messages import AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from 공통 import (ALLOWED, CODE_RUNNER, DAY_DIR, FILESYSTEM, METRICS_PATH, OUTPUT_DIR,
                SQLITE, SYSTEM_BASE, load_api_key)

load_api_key(DAY_DIR)   # 모델을 부르는 문제라 키를 맨 앞에서 확인한다

Q4 = "장르별 매출 합계에서 가장 매출이 큰 장르와 그 매출 합계를 알려줘."


class AnalysisResult(BaseModel):
    """분석 답변을 담는 정해진 틀 - 지표 이름·핵심 수치·한 문장 해석."""
    metric: str = Field(description="분석한 지표의 이름(예: '매출 1위 장르의 매출 합계')")
    value: float = Field(description="핵심 수치 하나(합계·평균·비율 등)")
    interpretation: str = Field(description="수치에 대한 한 문장 해석")


async def main():
    # [제공 코드] 지난 실행이 남긴 파일을 지운다. 이번 실행이 만든 것만 채점하기 위해서다.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.unlink(missing_ok=True)

    # 문제 4. 자유 문장으로 온 답을 정해진 틀에 담아 JSON 으로 남기기
    client = MultiServerMCPClient({"db": SQLITE, "code": CODE_RUNNER, "files": FILESYSTEM},
                                  tool_name_prefix=True)
    tools = [t for t in await client.get_tools() if t.name in ALLOWED]

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60)
    agent = create_agent(
        model, tools,
        middleware=[ModelCallLimitMiddleware(run_limit=8, exit_behavior="end")],
        system_prompt=SYSTEM_BASE,
    )

    # 1단계: 에이전트가 평소처럼 문장으로 답한다.
    result = await agent.ainvoke({"messages": Q4})
    answer_text = result["messages"][-1].text
    print("[에이전트 답변]", answer_text)

    # 2단계: 그 문장을 정해진 틀로 바꾼다. 도구 없이 한 번만 부르므로 결과가 일정하다.
    info = model.with_structured_output(AnalysisResult).invoke(answer_text)
    print("지표:", info.metric, "/ 수치:", info.value, f"({type(info.value).__name__})")
    print("해석:", info.interpretation)

    # 정형화의 목적은 적재다. 딕셔너리를 모으면 표가 되고, 표는 JSON 으로 남는다.
    metrics_df = pd.DataFrame([info.model_dump()])
    metrics_df.to_json(METRICS_PATH, orient="records", force_ascii=False)

    # [자가채점]
    called = [c["name"] for m in result["messages"] if isinstance(m, AIMessage) for c in (m.tool_calls or [])]
    assert "db_read_query" in called, f"에이전트가 DB 를 조회하지 않았습니다: {called}"
    assert "Rock" in answer_text, f"에이전트 답변에 매출 1위 장르가 없습니다: {answer_text[:200]}"
    assert 800 < info.value < 850, f"매출 1위 장르의 합계가 아닙니다: {info.value}"
    assert "Rock" in (info.metric + info.interpretation), \
        f"매출 1위 장르가 지표·해석에 없습니다: {info.metric} / {info.interpretation}"
    assert len(metrics_df) == 1, f"표는 한 행이어야 합니다: {len(metrics_df)}행"
    saved = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    assert isinstance(saved, list) and set(saved[0]) == {"metric", "value", "interpretation"}, \
        f"저장된 JSON 의 모양이 다릅니다: {saved}"
    print("문제 4 통과 -- 지표:", info.metric, "/ 수치:", info.value)
    print("저장:", METRICS_PATH)


if __name__ == "__main__":
    asyncio.run(main())
