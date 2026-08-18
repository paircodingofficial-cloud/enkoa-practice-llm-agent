"""📝 과제 문제 3: 자유 문장으로 온 답을 정해진 틀에 담아 JSON 으로 남기기

`# 여기에 코드를 작성하세요` 자리를 채우고 이 파일을 실행하세요.
아래 `# [자가채점]` 이 답을 검사하고, 통과하면 "문제 3 통과" 가 찍힙니다.
`계획을 세우지 않았습니다` 로 멈추면 코드가 틀린 것이 아닐 수 있습니다. 한 단계로 끝나는 질문이라
모델이 `write_todos` 를 건너뛰는 실행이 가끔 있습니다. 미들웨어를 넘겼다면 그대로 다시 실행하세요.

실습 04 는 `create_agent(response_format=...)` 로 답을 처음부터 틀에 받았습니다.
이 문제는 반대쪽 방법을 연습합니다. 에이전트는 평소처럼 문장으로 답하게 두고, 그 문장을
`with_structured_output` 으로 틀에 옮겨 담습니다. 에이전트가 아닌 아무 텍스트에도 쓸 수 있는 방법이라
둘 다 손에 익혀 둡니다.

준비물: OPENAI_API_KEY(일차 폴더 .env) · npx(Node.js) · uvx(uv)
실행: 이 파일이 있는 폴더에서  uv run 문제3_결과_정형화.py
"""

import asyncio
import json

import pandas as pd
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, TodoListMiddleware
from langchain_core.messages import AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from 공통 import (ALLOWED, DAY_DIR, METRICS_PATH, OUTPUT_DIR, PLAN_RULE, SQLITE,
                SYSTEM_BASE, load_api_key)

load_api_key(DAY_DIR)   # 모델을 부르는 문제라 키를 맨 앞에서 확인한다

# 뒤 문장으로 도구 범위를 좁힌다. 이 말이 없으면 모델이 code_run-code 로 계산까지 하려 들다
# 같은 코드를 되풀이하며 호출 상한을 다 쓴다(실제로 그렇게 끝난 적이 있다).
# 다만 "한 번이면 끝난다" 처럼 단계 수를 말하면 안 된다. 모델이 계획을 세울 이유가 없다고 보고
# write_todos 를 건너뛴다(이 역시 실제로 그랬다).
Q4 = ("장르별 매출 합계에서 가장 매출이 큰 장르와 그 매출 합계를 알려줘. "
      "표 조회로 구하는 값이라 계산도 그래프도 파일 저장도 필요 없다.")


async def main():
    # [제공 코드] 지난 실행이 남긴 파일을 지운다. 이번 실행이 만든 것만 채점하기 위해서다.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.unlink(missing_ok=True)

    # 문제 1. 자유 문장으로 온 답을 정해진 틀에 담아 JSON 으로 남기기
    #   - 답을 담을 틀을 pydantic 으로 만드세요. 클래스 이름은 `AnalysisResult` 이고 필드는 셋입니다.
    #       metric: str          분석한 지표의 한국어 이름
    #       value: float         핵심 수치 하나
    #       interpretation: str  수치에 대한 한 문장 해석
    #     각 필드에는 Field(description=...) 로 어떤 값인지 적어 주세요. 모델이 그 설명을 보고 채웁니다.
    #   - 이 문제는 DB 조회만 하면 되므로 MCP 서버는 db 하나만 띄웁니다.
    #     MultiServerMCPClient({"db": SQLITE}, tool_name_prefix=True) 로 붙어 get_tools() 를 await 한 뒤,
    #     이름이 `ALLOWED` 에 있는 도구만 남겨 변수 `tools` 에 담으세요.
    #     앞 문제처럼 코드 실행 서버까지 붙이면 모델이 SQL 대신 code_run-code 안에서 sqlite3 로
    #     DB 에 붙으려다 실패하고, 같은 코드를 되풀이하다 호출 상한에서 끝나는 일이 잦습니다.
    #     넘기지 않은 도구는 모델이 존재조차 모릅니다. 권한은 말이 아니라 목록으로 줍니다.
    #   - 모델은 앞 문제와 같은 ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60) 인데,
    #     아래 2단계에서 다시 쓰므로 변수에 담아 두세요.
    #     미들웨어는 앞 문제와 같이 TodoListMiddleware() 와
    #     ModelCallLimitMiddleware(run_limit=20, exit_behavior="end") 둘을 넘기고,
    #     시스템 프롬프트는 `SYSTEM_BASE + PLAN_RULE` 로 만드세요.
    #     앞 문제와 같은 구성으로 두는 것입니다. 다만 조회 한 번이면 되는 질문이라 모델이 계획을
    #     건너뛸 때도 있습니다. 계획 여부는 채점하지 않으니 기록에서 눈으로만 확인하세요.
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
    # 계획을 세웠는지는 채점하지 않는다. 조회 한 번이면 되는 질문이라 모델이 계획을 건너뛰기도 한다.
    # 미들웨어를 붙여도 무엇을 계획할지는 모델이 정한다는 것을 여기서 눈으로 본다.
    print("계획을 세웠나?:", "write_todos" in called, "· 호출한 도구:", called)
    assert "db_read_query" in called, f"에이전트가 DB 를 조회하지 않았습니다: {called}"
    assert "Rock" in answer_text, f"에이전트 답변에 매출 1위 장르가 없습니다: {answer_text[:200]}"
    assert 800 < info.value < 850, f"매출 1위 장르의 합계가 아닙니다: {info.value}"
    assert "Rock" in (info.metric + info.interpretation), \
        f"매출 1위 장르가 지표·해석에 없습니다: {info.metric} / {info.interpretation}"
    assert len(metrics_df) == 1, f"표는 한 행이어야 합니다: {len(metrics_df)}행"
    saved = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    assert isinstance(saved, list) and set(saved[0]) == {"metric", "value", "interpretation"}, \
        f"저장된 JSON 의 모양이 다릅니다: {saved}"
    print("문제 3 통과 -- 지표:", info.metric, "/ 수치:", info.value)
    print("저장:", METRICS_PATH)


if __name__ == "__main__":
    asyncio.run(main())
