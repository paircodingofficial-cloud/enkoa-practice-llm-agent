"""📝 과제 문제 2: 코드 실행 서버를 에이전트에 붙여 스스로 계산하게 하기

`# 여기에 코드를 작성하세요` 자리를 채우고 이 파일을 실행하세요.
아래 `# [자가채점]` 이 답을 검사하고, 통과하면 "문제 2 통과" 가 찍힙니다.

MCP 도구는 비동기 전용이라 `await 도구.ainvoke({...})` 로 부릅니다.

준비물: OPENAI_API_KEY(일차 폴더 .env) · npx(Node.js)
실행: 이 파일이 있는 폴더에서  uv run 문제2_코드실행_에이전트.py
"""

import asyncio

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain_core.messages import AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

from 공통 import CODE_RUNNER, DAY_DIR, load_api_key
from utils import print_trajectory   # 공통.py 가 일차 폴더를 경로에 넣어 둔다

load_api_key(DAY_DIR)   # 모델을 부르는 문제라 키를 맨 앞에서 확인한다

Q2 = "1 부터 100 까지 더하면 얼마인지 알려 줘. 암산하지 말고 반드시 코드를 실행해서 계산해."


async def main():
    # 문제 2. 코드 실행 서버를 에이전트에 붙여 스스로 계산하게 하기
    #   - CODE_RUNNER 로 도구 목록을 받아 변수 `code_tools` 에 담으세요.
    #   - 그 도구를 create_agent 에 넘겨 에이전트를 만드세요.
    #     모델은 ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60) 입니다.
    #   - 시스템 프롬프트에 이 둘을 적으세요.
    #       1) 수치 계산은 반드시 코드 실행 도구로 한다
    #       2) 코드의 결과는 print 로 출력해야 값이 돌아온다(결과가 비면 print 를 빠뜨린 것이다)
    #   - middleware=[ModelCallLimitMiddleware(run_limit=8, exit_behavior="end")] 를 함께 넘기세요.
    #     모델이 같은 호출을 반복해도 상한에서 스스로 끝납니다.
    #   - 위 `Q2` 를 물어 결과를 변수 `result` 에 담고, print_trajectory(result) 로 기록을 찍으세요.
    # 여기에 코드를 작성하세요

    # [자가채점]
    called = [c["name"] for m in result["messages"] if isinstance(m, AIMessage) for c in (m.tool_calls or [])]
    answer = result["messages"][-1].text
    assert any("run-code" in name for name in called), f"코드 실행 도구를 쓰지 않았습니다: {called}"
    assert "5050" in answer, f"답에 5050 이 없습니다: {answer[:120]}"
    print("문제 2 통과 -- 호출한 도구:", called)


if __name__ == "__main__":
    asyncio.run(main())
