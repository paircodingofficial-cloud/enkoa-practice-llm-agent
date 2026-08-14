"""📝 과제 문제 2 정답: TodoListMiddleware 로 복합 요청에 계획을 세우게 하기

준비물: OPENAI_API_KEY(일차 폴더 .env) · npx(Node.js) · uvx(uv)
실행: 이 파일이 있는 폴더에서  uv run 문제2_계획_에이전트_정답.py
"""

import asyncio
import sys
from pathlib import Path

# 실습 폴더의 과제 파일들이 함께 쓰는 공통.py 를 그대로 씁니다
sys.path.append(str(Path(__file__).resolve().parents[3] / "day21_Agent_데이터분석_자동화" / "교안_02_계획_실행_자동화" / "과제"))

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, TodoListMiddleware
from langchain_core.messages import AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

from 공통 import (ALLOWED, CODE_RUNNER, DAY_DIR, FILESYSTEM, PLAN_RULE, SQLITE,
                SYSTEM_BASE, load_api_key)
from utils import print_trajectory   # 공통.py 가 일차 폴더를 경로에 넣어 둔다

load_api_key(DAY_DIR)   # 모델을 부르는 문제라 키를 맨 앞에서 확인한다

Q2 = ("chinook DB 에서 고객이 가장 많은 국가 상위 5개와 각 국가의 고객 수를 구하고, "
      "그 5개국이 전체 고객에서 차지하는 비중(%)도 계산해줘.")


async def main():
    # 문제 2. TodoListMiddleware 로 복합 요청에 계획을 세우게 하기
    client = MultiServerMCPClient({"db": SQLITE, "code": CODE_RUNNER, "files": FILESYSTEM},
                                  tool_name_prefix=True)
    tools = [t for t in await client.get_tools() if t.name in ALLOWED]

    system_plan = SYSTEM_BASE + PLAN_RULE   # 계획을 먼저 세우라고 시키는 한 문장
    agent = create_agent(
        ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60),
        tools,
        # 계획 도구(write_todos)는 우리가 넘긴 목록이 아니라 이 미들웨어가 붙여 준다
        middleware=[TodoListMiddleware(),
                    ModelCallLimitMiddleware(run_limit=30, exit_behavior="end")],
        system_prompt=system_plan,
    )
    result = await agent.ainvoke({"messages": Q2})
    print_trajectory(result)

    # 계획을 세우지 않은 실행도 있을 수 있으므로 get 으로 안전하게 꺼낸다
    todos = result.get("todos", [])
    print("\n---- 세운 계획과 진행 상태 ----")
    for item in todos:
        print(f"- [{item['status']}] {item['content']}")

    # [자가채점]
    called = [c["name"] for m in result["messages"] if isinstance(m, AIMessage) for c in (m.tool_calls or [])]
    answer = result["messages"][-1].text
    # write_todos 는 부를 때마다 계획 전체를 새로 쓴다. 그래서 마지막 상태(todos)만 보면
    # 처음 세운 계획이 몇 단계였는지 알 수 없다. 호출 기록에서 계획들을 그대로 꺼내 본다.
    plans = [c["args"]["todos"] for m in result["messages"] if isinstance(m, AIMessage)
             for c in (m.tool_calls or []) if c["name"] == "write_todos"]
    assert plans, f"계획을 세우지 않았습니다: {called}"
    assert any(len(plan) >= 2 for plan in plans), f"계획이 너무 짧습니다: {plans}"
    done = sum(item["status"] == "completed" for item in todos)
    assert "db_read_query" in called, f"DB 를 조회하지 않았습니다: {called}"
    assert "USA" in answer or "미국" in answer, \
        f"고객이 가장 많은 국가가 답에 없습니다: {answer[:200]}"
    print("문제 2 통과 -- 처음 세운 계획", len(plans[0]), "단계 · 호출한 도구:", called)
    # 계획을 세우는 것과 상태를 끝까지 갱신하는 것은 다른 일이다. 모델은 계획만 세우고
    # 상태를 그대로 두기도 한다. 그래서 채점은 계획을 세웠는지까지만 보고, 갱신은 눈으로 본다.
    print("완료로 표시된 단계:", done, "/", len(todos))


if __name__ == "__main__":
    asyncio.run(main())
