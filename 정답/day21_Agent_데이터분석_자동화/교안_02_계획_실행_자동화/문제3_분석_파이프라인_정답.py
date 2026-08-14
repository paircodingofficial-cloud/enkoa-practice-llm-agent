"""📝 과제 문제 3 정답: 조회 -> 계산 -> 그래프 -> 리포트 파이프라인 자동화하기

준비물: OPENAI_API_KEY(일차 폴더 .env) · npx(Node.js) · uvx(uv)
실행: 이 파일이 있는 폴더에서  uv run 문제3_분석_파이프라인_정답.py
"""

import asyncio
import re
import sys
from pathlib import Path

# 실습 폴더의 과제 파일들이 함께 쓰는 공통.py 를 그대로 씁니다
sys.path.append(str(Path(__file__).resolve().parents[3] / "day21_Agent_데이터분석_자동화" / "교안_02_계획_실행_자동화" / "과제"))

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, TodoListMiddleware
from langchain_core.messages import AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

from 공통 import (ALLOWED, CHART_NAME, CHART_PATH, CODE_RUNNER, DAY_DIR, FILESYSTEM,
                OUTPUT_DIR, PLAN_RULE, REPORT_NAME, REPORT_PATH, SQLITE, SYSTEM_BASE,
                load_api_key)
from utils import print_trajectory   # 공통.py 가 일차 폴더를 경로에 넣어 둔다

load_api_key(DAY_DIR)   # 모델을 부르는 문제라 키를 맨 앞에서 확인한다

Q3 = (
    "1) invoice_items 와 tracks, genres 를 이어 장르별 매출 합계 상위 10개를 조회하고, "
    "2) 그중 상위 3개 장르가 전체 매출에서 차지하는 비중(%)을 계산하고"
    "(전체 매출은 상위 10개의 합이 아니라 모든 장르의 매출 합계다), "
    f"3) 상위 10개 장르의 매출 막대그래프를 {CHART_NAME} 로 저장하고, "
    f"4) 위 결과를 정리한 마크다운 리포트를 {REPORT_NAME} 에 저장해줘. "
    "그래프는 matplotlib 을 쓰되 창을 띄우지 말고(Agg) 한글 폰트를 지정해서 저장해. "
    "리포트에는 상위 10개 장르의 매출 표와 상위 3개 장르의 비중을 숫자로 적어줘."
)


async def main():
    # [제공 코드] 지난 실행이 남긴 산출물을 지운다. 이번 실행이 만든 것만 채점하기 위해서다.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHART_PATH.unlink(missing_ok=True)
    REPORT_PATH.unlink(missing_ok=True)

    # 문제 3. 조회 -> 계산 -> 그래프 -> 리포트 파이프라인 자동화하기
    client = MultiServerMCPClient({"db": SQLITE, "code": CODE_RUNNER, "files": FILESYSTEM},
                                  tool_name_prefix=True)
    tools = [t for t in await client.get_tools() if t.name in ALLOWED]

    system_plan = SYSTEM_BASE + PLAN_RULE   # 계획을 먼저 세우라고 시키는 한 문장
    agent = create_agent(
        ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60),
        tools,
        middleware=[TodoListMiddleware(),
                    ModelCallLimitMiddleware(run_limit=30, exit_behavior="end")],
        system_prompt=system_plan,
    )
    result = await agent.ainvoke({"messages": Q3})
    print_trajectory(result)

    print()
    # 모델의 '저장했습니다' 라는 말이 아니라 파일로 확인한다
    for path in (CHART_PATH, REPORT_PATH):
        size = path.stat().st_size if path.exists() else 0
        print(f"{path.name:24} 있음={path.exists()} 크기={size}")

    # [자가채점]
    called = [c["name"] for m in result["messages"] if isinstance(m, AIMessage) for c in (m.tool_calls or [])]
    assert "db_read_query" in called, f"DB 를 조회하지 않았습니다: {called}"
    assert "code_run-code" in called, f"계산·그래프를 코드로 하지 않았습니다: {called}"
    assert "files_write_file" in called, f"리포트를 파일로 저장하지 않았습니다: {called}"
    assert CHART_PATH.exists(), f"{CHART_PATH} 가 없습니다"
    assert CHART_PATH.read_bytes()[:4] == b"\x89PNG", \
        "PNG 그림이 아닙니다. 그림은 files_write_file 이 아니라 코드 실행 도구의 savefig 로 저장해야 합니다"
    assert CHART_PATH.stat().st_size > 1000, "그래프 파일이 너무 작습니다. 그림이 저장되지 않았습니다"
    assert REPORT_PATH.exists(), f"{REPORT_PATH} 가 없습니다"
    report = REPORT_PATH.read_text(encoding="utf-8")
    assert "Rock" in report, f"매출 1위 장르가 리포트에 없습니다: {report[:200]}"
    percents = [float(x) for x in re.findall(r"(\d{1,3}(?:\.\d+)?)\s*%", report)]
    assert percents, f"비중(%)이 숫자로 리포트에 적히지 않았습니다: {report[:300]}"
    print("문제 3 통과 -- 호출한 도구:", called)
    # 비중을 데이터로 계산하면 63.1% 다. 리포트의 값과 견줘 보고, 다르면 기록에서
    # 모델이 무엇을 분모로 삼았는지 찾아보자.
    print("리포트가 적은 비중:", percents, "/ 데이터로 계산한 값: 63.1%")
    print("그래프:", CHART_PATH, "/ 리포트:", REPORT_PATH)


if __name__ == "__main__":
    asyncio.run(main())
