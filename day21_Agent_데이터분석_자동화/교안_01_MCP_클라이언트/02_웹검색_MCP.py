"""교안 01-2: 웹 검색 MCP 서버 붙이기

핵심 목표
    웹 검색 서버를 에이전트에 붙여, 모델이 스스로 검색하고 근거 URL 까지 밝히게 만든다.

학습 순서
    1) 검색 서버(duckduckgo-mcp-server) 연결과 도구 두 개(search·fetch_content)
    2) 검색 도구 직접 호출
    3) 본문 가져오기
    4) 검색 도구를 붙인 에이전트 -- 근거 URL 까지 답하게 하기

쓰는 MCP 서버와 공식 문서
    웹 검색 서버 duckduckgo-mcp-server
        https://github.com/nickclyde/duckduckgo-mcp-server

실행: 이 파일이 있는 폴더에서  uv run 02_웹검색_MCP.py

에이전트를 만드는 절부터 OPENAI_API_KEY 가 필요합니다(일차 폴더의 .env).
서버가 남기는 로그가 출력 사이에 섞일 수 있습니다 -- 서버는 우리가 띄운 자식 프로세스라 화면을 같이 씁니다.
"""

import asyncio
import sys
from pathlib import Path

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI

sys.path.append(str(Path(__file__).resolve().parent.parent))   # 일차 폴더의 utils.py 를 쓴다

from utils import load_api_key, print_trajectory


DAY_DIR = Path(__file__).resolve().parent.parent    # 일차 폴더(day21). 아래 경로들의 기준점

load_api_key(DAY_DIR)   # 모델을 부르는 절이 있으므로 키를 맨 앞에서 확인한다

# 웹 검색 서버: 검색 결과 목록과 페이지 본문을 가져오는 도구를 내준다. API 키가 필요 없다.
WEB_SEARCH = {
    "command": "uvx",                       # 파이썬 패키지를 받아 실행하는 실행기(uv 에 딸려 온다)
    "args": ["duckduckgo-mcp-server"],      # 띄울 서버 패키지 이름
    "transport": "stdio",                   # 내 컴퓨터에 프로세스로 띄운다
}


async def ask(agent, question):
    """에이전트에게 질문한다. 도구 하나라도 MCP 면 에이전트도 ainvoke 로 불러야 한다.

    질문 문자열만 넘기면 LangChain 이 사람 메시지(HumanMessage)로 바꿔 준다.
    """
    return await agent.ainvoke({"messages": question})


async def main():
    print("\n=== 1. 검색 서버에 붙기 ===")
    # "search" 는 우리가 이 서버에 붙이는 별명이다 -- 서버가 여럿일 때 구분하려고 쓴다.
    print("서버를 띄우는 중입니다(첫 실행은 오래 걸립니다)...")
    client = MultiServerMCPClient({"search": WEB_SEARCH})

    # session 을 열어 둔 채 그 안에서 도구를 부른다. 서버는 이 블록 동안만 살아 있다.
    async with client.session("search") as session:
        tools = await load_mcp_tools(session)
        by_name = {tool.name: tool for tool in tools}   # 이름으로 꺼내 쓰려고 딕셔너리로

        # 이 서버가 내주는 도구를 '이름(인자): 설명 첫 줄' 로 찍어 무엇을 할 수 있는지 확인한다.
        print(f"도구 {len(tools)}개")
        for tool in tools:
            print(f" - {tool.name}({', '.join(tool.args)}): {tool.description.strip().splitlines()[0][:60]}")

        print("\n=== 2. 검색 도구를 직접 호출하기 ===")
        # search: 검색어를 받아 제목·요약·링크를 돌려주는 도구. max_results 가 클수록 에이전트가 읽을 토큰도 늘어난다.
        found = await by_name["search"].ainvoke({"query": "MCP Model Context Protocol 개념", "max_results": 3})
        print(found[0]["text"][:800])

        print("\n=== 3. 본문 가져오기 ===")
        # fetch_content: URL 하나를 받아 본문 텍스트를 돌려주는 도구. 검색 결과는 제목·요약뿐이라 이 도구로 이어 붙인다.
        body = (await by_name["fetch_content"].ainvoke(
            {"url": "https://modelcontextprotocol.io/docs/getting-started/intro"}))[0]["text"]
        print("가져온 글자 수:", len(body))
        print(body[:500])

        print("\n=== 4. 검색 도구를 에이전트에 붙이기 ===")
        # 여기서부터는 우리가 도구를 직접 부르지 않는다. 무엇을 부를지 모델이 정한다.
        model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        # 언제 도구를 쓸지와 출처를 어떻게 남길지를 못 박는다. 안 그러면 모델이 검색 없이 아는 척 답한다.
        agent = create_agent(
            model,
            tools,   # MCP 도구를 그대로 넘긴다 -- 우리가 만든 도구와 같은 자리다
            system_prompt=(
                "너는 조사 담당이다. 사실 확인이 필요하면 반드시 search 도구로 검색하고, "
                "요약만으로 부족하면 fetch_content 로 본문까지 읽어 확인한 뒤 답한다. "
                "답의 문장마다 근거가 된 페이지의 URL 을 괄호로 붙이고, 맨 끝에 '참고한 주소' 목록을 "
                "'- 제목: URL' 형태로 정리한다. 검색 결과에 없는 내용은 쓰지 않고, "
                "확인하지 못한 부분은 확인하지 못했다고 밝힌다."
            ),
        )

        question = "Model Context Protocol 은 무엇이고 어디에 쓰나요? 웹에서 찾아 3문장으로 정리해 주세요."
        print("질문:", question, "\n")
        # 메시지 기록을 함께 찍는다. 모델이 검색을 실제로 했는지는 이 기록으로만 확인할 수 있다.
        print_trajectory(await ask(agent, question))


# 이 파일을 직접 실행할 때만 main 을 돌린다(다른 파일이 import 해도 실행되지 않게).
if __name__ == "__main__":
    asyncio.run(main())
