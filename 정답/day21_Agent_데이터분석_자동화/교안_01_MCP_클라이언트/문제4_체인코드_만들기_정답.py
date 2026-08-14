"""📝 과제 문제 4 정답: 문서 조회·코드 실행·우리 도구를 한 에이전트에 묶어 체인 코드 만들기

준비물: OPENAI_API_KEY(일차 폴더 .env) · npx(Node.js) · 인터넷
실행: 이 파일이 있는 폴더에서  uv run 문제4_체인코드_만들기_정답.py
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
    context7 = {"url": "https://mcp.context7.com/mcp", "transport": "streamable_http"}
    docs_tools = await MultiServerMCPClient({"docs": context7}).get_tools()
    code_tools = await MultiServerMCPClient({"code": CODE_RUNNER}).get_tools()

    agent = create_agent(
        ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60),
        # 남의 문서(Context7) · 남의 실행기(run-code) · 우리 규칙(team_llm_rule)이 한 손에 들어온다.
        [*docs_tools, *code_tools, team_llm_rule],
        system_prompt=(
            "너는 LangChain 코드를 쓰는 담당이다. "
            "LangChain API 는 기억으로 쓰지 말고 resolve-library-id 와 query-docs 로 최신 문서를 "
            "확인한 뒤 그 문서에 나오는 API 만 쓴다. "
            "문서를 찾을 때는 'ChatPromptTemplate StrOutputParser chain' 처럼 만들 것을 그대로 묻는다. "
            "문서에 에이전트 예시가 많이 나오지만 이번에 만들 것은 에이전트가 아니라 체인이다. "
            "모델 이름과 온도는 team_llm_rule 로 확인해 그 값을 그대로 쓴다. "
            "코드를 다 쓰면 run-code 도구로 compile(코드, 'basic_chain.py', 'exec') 를 돌려 문법을 검사하고, "
            "코드에서는 결과를 print 로 출력해야 값이 돌아온다. 결과가 비면 print 를 빠뜨린 것이다. "
            "최종 답에는 설명 없이 완성된 코드 하나만 ```python 코드블록으로 넣는다."
        ),
        middleware=[ModelCallLimitMiddleware(run_limit=15, exit_behavior="end")],
    )
    result = await agent.ainvoke({"messages": Q4})
    print_trajectory(result)

    chain_code = extract_code(result["messages"][-1].text)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHAIN_PATH.write_text(chain_code, encoding="utf-8")

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
