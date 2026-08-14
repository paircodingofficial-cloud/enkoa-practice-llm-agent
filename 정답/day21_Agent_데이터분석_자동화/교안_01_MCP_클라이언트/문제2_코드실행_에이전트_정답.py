"""📝 과제 문제 2 정답: 코드 실행 서버를 에이전트에 붙여 스스로 계산하게 하기

준비물: OPENAI_API_KEY(일차 폴더 .env) · npx(Node.js)
실행: 이 파일이 있는 폴더에서  uv run 문제2_코드실행_에이전트_정답.py
"""

import asyncio
import sys
from pathlib import Path

# 실습 폴더의 과제 파일들이 함께 쓰는 공통.py 를 그대로 씁니다
sys.path.append(str(Path(__file__).resolve().parents[3] / "day21_Agent_데이터분석_자동화" / "교안_01_MCP_클라이언트" / "과제"))

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
    code_tools = await MultiServerMCPClient({"code": CODE_RUNNER}).get_tools()
    agent = create_agent(
        ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60),
        code_tools,
        system_prompt=(
            "너는 계산 도우미다. 수치 계산은 반드시 코드 실행 도구로 계산한 뒤 그 결과로 답한다. "
            "코드의 결과에 대한 마지막 줄은 반드시 print 로 출력한다. "
            "결과가 비어 있으면 print 를 빠뜨린 것이니 print 를 넣어 다시 실행한다."
        ),
        middleware=[ModelCallLimitMiddleware(run_limit=8, exit_behavior="end")],
    )
    result = await agent.ainvoke({"messages": Q2})
    print_trajectory(result)

    # [자가채점]
    called = [c["name"] for m in result["messages"] if isinstance(m, AIMessage) for c in (m.tool_calls or [])]
    answer = result["messages"][-1].text
    assert any("run-code" in name for name in called), f"코드 실행 도구를 쓰지 않았습니다: {called}"
    assert "5050" in answer, f"답에 5050 이 없습니다: {answer[:120]}"
    print("문제 2 통과 -- 호출한 도구:", called)


if __name__ == "__main__":
    asyncio.run(main())
