"""📝 과제 문제 3 정답: 원격(HTTP) 문서 서버 Context7 을 에이전트에 붙여 최신 문서를 찾게 하기

준비물: OPENAI_API_KEY(일차 폴더 .env) · 인터넷
실행: 이 파일이 있는 폴더에서  uv run 문제3_원격문서조회_에이전트_정답.py
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

from 공통 import DAY_DIR, load_api_key
from utils import print_trajectory   # 공통.py 가 일차 폴더를 경로에 넣어 둔다

load_api_key(DAY_DIR)   # 모델을 부르는 문제라 키를 맨 앞에서 확인한다

Q3 = (
    "LangChain 에서 프롬프트 템플릿과 채팅 모델, 문자열 출력 파서를 이어 붙이는 기초 체인은 "
    "지금 버전에서 어떻게 쓰는지 알려 줘. 기억으로 답하지 말고 문서 도구로 확인한 뒤 답해."
)


async def main():
    # 문제 3. 원격(HTTP) 문서 서버 Context7 을 에이전트에 붙여 최신 문서를 찾게 하기
    context7 = {"url": "https://mcp.context7.com/mcp", "transport": "streamable_http"}   # 원격은 url 만
    docs_tools = await MultiServerMCPClient({"docs": context7}).get_tools()
    agent = create_agent(
        ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60),
        docs_tools,
        system_prompt=(
            "너는 라이브러리 사용법을 알려 주는 도우미다. "
            "먼저 resolve-library-id 로 라이브러리 ID 를 찾고, 그 ID 로 query-docs 를 불러 문서를 받는다. "
            "문서에서 확인한 API 만 쓰고 기억으로 지어내지 않는다. "
            "답에는 문서에서 본 코드 예시를 함께 넣는다."
        ),
        middleware=[ModelCallLimitMiddleware(run_limit=8, exit_behavior="end")],
    )
    result = await agent.ainvoke({"messages": Q3})
    print_trajectory(result)

    # [자가채점]
    called = [c["name"] for m in result["messages"] if isinstance(m, AIMessage) for c in (m.tool_calls or [])]
    answer = result["messages"][-1].text
    assert context7.get("transport") == "streamable_http", "transport 가 streamable_http 여야 합니다"
    assert "command" not in context7, "원격 서버에는 command 를 쓰지 않습니다"
    assert any("resolve-library-id" in name for name in called), f"라이브러리 ID 를 찾지 않았습니다: {called}"
    assert any("query-docs" in name for name in called), f"문서 조회 도구를 쓰지 않았습니다: {called}"
    assert len(answer) > 100, f"답이 너무 짧습니다: {answer!r}"
    print("문제 3 통과 -- 호출한 도구:", called)


if __name__ == "__main__":
    asyncio.run(main())
