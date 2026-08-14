"""📝 과제 문제 4: 문서 조회·코드 실행·우리 도구를 한 에이전트에 묶어 체인 코드 만들기

`# 여기에 코드를 작성하세요` 자리를 채우고 이 파일을 실행하세요.
아래 `# [자가채점]` 이 답을 검사하고, 통과하면 "문제 4 통과" 가 찍힙니다.

MCP 도구는 비동기 전용이라 `await 도구.ainvoke({...})` 로 부릅니다.

준비물: OPENAI_API_KEY(일차 폴더 .env) · npx(Node.js) · 인터넷
실행: 이 파일이 있는 폴더에서  uv run 문제4_체인코드_만들기.py
"""

import asyncio
from contextlib import AsyncExitStack   # 세션 여럿을 한 블록에 쌓아 두고 한꺼번에 닫는다

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain_core.messages import AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools   # 열어 둔 세션에서 도구를 꺼낸다
from langchain_openai import ChatOpenAI

from 공통 import CHAIN_PATH, CODE_RUNNER, DAY_DIR, OUTPUT_DIR, load_api_key, team_llm_rule
from utils import extract_code, print_trajectory   # 공통.py 가 일차 폴더를 경로에 넣어 둔다

load_api_key(DAY_DIR)   # 모델을 부르는 문제라 키를 맨 앞에서 확인한다

Q4 = (
    "LangChain 으로 기초적인 체인을 만드는 파이썬 코드를 작성해 줘. "
    "에이전트(create_agent)가 아니라 ChatPromptTemplate · 채팅 모델 · StrOutputParser 를 "
    "파이프(|)로 이은 체인이어야 해. 거기에 질문 하나를 넣어 invoke 로 부르고 결과를 print 하면 돼. "
    "그 세 가지를 지금 버전에서 어떻게 쓰는지 Context7 문서로 확인한 뒤 그 API 만 쓰고, "
    "모델 이름과 온도는 우리 팀 규칙 도구로 확인해서 그 값을 그대로 써. "
    "완성한 코드는 코드 실행 도구로 문법 검사를 한 뒤 최종 코드만 코드블록으로 보여 줘."
)


async def main():
    # 문제 4. 문서 조회·코드 실행·우리 도구를 한 에이전트에 묶어 체인 코드 만들기
    #   - 문제 3 의 Context7 설정과 문제 2 의 CODE_RUNNER 를 한 클라이언트에 함께 등록하세요.
    #     (MultiServerMCPClient({"docs": context7, "code": CODE_RUNNER}))
    #   - 서버가 둘이라 async with 를 두 겹 겹쳐야 합니다. 대신 `async with AsyncExitStack() as stack:`
    #     한 블록을 열고, 서버마다
    #         session = await stack.enter_async_context(client.session(서버이름))
    #     로 세션을 쌓은 뒤 `await load_mcp_tools(session)` 으로 도구를 모으세요.
    #     블록이 끝나면 연 순서의 역순으로 두 서버가 알아서 닫힙니다.
    #   - 모은 도구와 위에서 불러 온 `team_llm_rule` 을 한 리스트로 합쳐 create_agent 에 넘기세요.
    #     모델은 ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60) 입니다.
    #   - 시스템 프롬프트에는 이 셋을 넣으세요.
    #       1) LangChain API 는 기억에 의존하지 말고 Context7 도구로 최신 문서를 확인한 뒤 쓴다
    #          (문서에는 에이전트 예시가 많으니 "체인"을 만들라고 못 박아 두세요)
    #       2) 모델 이름과 온도는 team_llm_rule 로 확인해 그 값을 그대로 쓴다
    #       3) 완성한 코드는 run-code 도구로 문법 검사까지 한 뒤, 최종 답에는 코드 하나만
    #          ```python 코드블록으로 넣는다(이 서버는 print 로 찍은 것만 돌려줍니다)
    #   - middleware=[ModelCallLimitMiddleware(run_limit=15, exit_behavior="end")] 를 함께 넘기세요.
    #   - 위 `Q4` 를 물어 결과를 변수 `result` 에 담고, print_trajectory(result) 로 기록을 찍으세요.
    #     (여기까지가 블록 안입니다. 아래 저장은 블록 밖에서 해도 됩니다.)
    #   - 최종 답변 텍스트에서 extract_code(...) 로 코드만 꺼내 변수 `chain_code` 에 담고,
    #     OUTPUT_DIR.mkdir(parents=True, exist_ok=True) 로 저장할 폴더를 먼저 만든 뒤
    #     CHAIN_PATH 에 저장하세요(파일 쓰기는 CHAIN_PATH.write_text(chain_code, encoding="utf-8") 입니다).
    # 여기에 코드를 작성하세요

    # [자가채점]
    called = [c["name"] for m in result["messages"] if isinstance(m, AIMessage) for c in (m.tool_calls or [])]
    assert any("query-docs" in name or "resolve-library-id" in name for name in called), \
        f"Context7 문서 도구를 쓰지 않았습니다: {called}"
    assert any("run-code" in name for name in called), f"코드 실행 도구를 쓰지 않았습니다: {called}"
    assert any("team_llm_rule" in name for name in called), f"우리 도구를 쓰지 않았습니다: {called}"
    # 코드의 생김새는 모델이 매번 다르게 쓴다. 그래서 '체인 모양'을 글자로 맞추는 대신,
    # 문서·우리 규칙·문법 검사라는 이 문제의 알맹이가 결과에 남았는지만 본다.
    assert "langchain" in chain_code.lower(), f"LangChain 코드가 아닙니다: {chain_code[:120]}"
    assert "invoke" in chain_code, "만든 것을 invoke 로 부르는 코드가 아닙니다"
    assert "gpt-4o-mini" in chain_code, "우리 팀 규칙의 모델 이름이 코드에 없습니다"
    compile(chain_code, "basic_chain.py", "exec")                  # 문법이 맞는지 여기서 확인한다
    assert CHAIN_PATH.exists(), f"{CHAIN_PATH} 에 저장되지 않았습니다"
    assert CHAIN_PATH.read_text(encoding="utf-8").strip() == chain_code.strip(), \
        f"{CHAIN_PATH} 의 내용이 이번에 만든 코드와 다릅니다(예전 실행이 남은 파일일 수 있습니다)"
    print("문제 4 통과 -- 호출한 도구:", called)
    print("체인 코드 저장:", CHAIN_PATH)


if __name__ == "__main__":
    asyncio.run(main())
