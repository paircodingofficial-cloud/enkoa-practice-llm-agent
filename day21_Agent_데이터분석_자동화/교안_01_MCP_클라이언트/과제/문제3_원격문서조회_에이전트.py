"""📝 과제 문제 3: 원격(HTTP) 문서 서버 Context7 을 에이전트에 붙여 최신 문서를 찾게 하기

`# 여기에 코드를 작성하세요` 자리를 채우고 이 파일을 실행하세요.
아래 `# [자가채점]` 이 답을 검사하고, 통과하면 "문제 3 통과" 가 찍힙니다.

MCP 도구는 비동기 전용이라 `await 도구.ainvoke({...})` 로 부릅니다.

준비물: OPENAI_API_KEY(일차 폴더 .env) · 인터넷
실행: 이 파일이 있는 폴더에서  uv run 문제3_원격문서조회_에이전트.py
"""

import asyncio

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
    #   - Context7 은 교안에서 다루지 않았습니다. 연결 설정을 직접 만듭니다.
    #     주소는 "https://mcp.context7.com/mcp" 이고 전송 방식은 "streamable_http" 입니다.
    #     원격 서버라 command·args 가 없고 url 을 씁니다(교안 개념 5절).
    #   - 만든 설정을 변수 `context7` 에 담고, 도구 목록을 받아 변수 `docs_tools` 에 담으세요.
    #   - 그 도구를 create_agent 에 넘겨 에이전트를 만드세요.
    #     모델은 ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60) 입니다.
    #   - 시스템 프롬프트에 이 둘을 적으세요.
    #       1) 먼저 resolve-library-id 로 라이브러리 ID 를 찾고 query-docs 로 문서를 받는다
    #       2) 문서에서 확인한 API 만 쓰고, 기억으로 지어내지 않는다
    #   - middleware=[ModelCallLimitMiddleware(run_limit=8, exit_behavior="end")] 를 함께 넘기세요.
    #   - 위 `Q3` 를 물어 결과를 변수 `result` 에 담고, print_trajectory(result) 로 기록을 찍으세요.
    # 여기에 코드를 작성하세요

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
