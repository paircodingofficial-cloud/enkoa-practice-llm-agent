"""📝 과제 문제 4: 자유 문장으로 온 답을 정해진 틀에 담아 JSON 으로 남기기

`# 여기에 코드를 작성하세요` 자리를 채우고 이 파일을 실행하세요.
아래 `# [자가채점]` 이 답을 검사하고, 통과하면 "문제 4 통과" 가 찍힙니다.

준비물: OPENAI_API_KEY(일차 폴더 .env) · npx(Node.js) · uvx(uv)
실행: 이 파일이 있는 폴더에서  uv run 문제4_결과_정형화.py
"""

import asyncio
import json

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


async def main():
    # [제공 코드] 지난 실행이 남긴 파일을 지운다. 이번 실행이 만든 것만 채점하기 위해서다.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.unlink(missing_ok=True)

    # 문제 4. 자유 문장으로 온 답을 정해진 틀에 담아 JSON 으로 남기기
    #   - 답을 담을 틀을 pydantic 으로 만드세요. 클래스 이름은 `AnalysisResult` 이고 필드는 셋입니다.
    #       metric: str          분석한 지표의 이름
    #       value: float         핵심 수치 하나
    #       interpretation: str  수치에 대한 한 문장 해석
    #     각 필드에는 Field(description=...) 로 어떤 값인지 적어 주세요. 모델이 그 설명을 보고 채웁니다.
    #   - 문제 2 처럼 도구를 골라 에이전트를 만드세요. 모델은 문제 2 와 같은
    #     ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60) 인데, 아래 2단계에서 다시 쓰므로
    #     변수에 담아 두세요. 이번에는 계획이 필요 없는 한 단계짜리 질문이라 미들웨어는
    #     ModelCallLimitMiddleware(run_limit=8, exit_behavior="end") 하나만 넘기고,
    #     시스템 프롬프트는 `SYSTEM_BASE` 를 그대로 씁니다.
    #   - 위 `Q4` 를 물어 결과를 변수 `result` 에 담고, 그 답의 마지막 메시지 글자를
    #     변수 `answer_text` 에 담아 print 하세요.
    #     (마지막 메시지는 result["messages"][-1] 이고 글자는 그 .text 입니다.)
    #   - 모델에 with_structured_output(AnalysisResult) 를 걸어 `answer_text` 를 넣고,
    #     돌아온 객체를 변수 `info` 에 담으세요. 도구 없이 한 번만 부르므로 결과가 일정합니다.
    #     원래 질문이 아니라 에이전트가 낸 문장을 넣는 것이 핵심입니다.
    #   - info.model_dump() 하나를 담은 pandas DataFrame 을 만들어 변수 `metrics_df` 에 담고,
    #     METRICS_PATH 에 to_json(orient="records", force_ascii=False) 로 저장하세요.
    #     orient="records" 는 행 하나를 객체 하나로, force_ascii=False 는 한글을 그대로 쓰는 옵션입니다.
    # 여기에 코드를 작성하세요

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
