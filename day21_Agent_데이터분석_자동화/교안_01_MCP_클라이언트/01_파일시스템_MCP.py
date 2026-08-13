"""교안 01-1: 파일시스템 MCP 서버 붙이기

개념은 같은 폴더의 `교안_01_MCP_개념.ipynb` 를 먼저 읽으세요.

핵심 목표
    남이 만들어 공개한 MCP 서버에 붙어, 우리가 한 줄도 만들지 않은 도구를 그대로 불러 쓴다.

학습 순서
    1) 파일시스템 MCP 서버에 붙어 도구 목록 받기
    2) 도구 명세(name·description·args) 읽기 -- 에이전트가 보는 정보와 같다
    3) 도구 직접 호출과 반환값의 원래 모양
    4) 반환값에서 사람이 읽을 부분(text) 꺼내기
    5) 허용된 폴더 밖은 막힌다
    6) 받은 도구를 LangChain 에이전트에 붙이기 -- 무엇을 부를지 모델이 정한다

쓰는 MCP 서버와 공식 문서
    파일시스템 서버 @modelcontextprotocol/server-filesystem
        https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem
    MCP 규격 자체
        https://modelcontextprotocol.io/docs/getting-started/intro

실행: 이 파일이 있는 폴더에서  uv run 01_파일시스템_MCP.py

첫 실행은 서버 패키지를 내려받느라 수십 초 걸릴 수 있습니다(두 번째부터 빠릅니다).
에이전트를 만드는 절부터 OPENAI_API_KEY 가 필요합니다(일차 폴더의 .env).
"""

import asyncio
import sys
from pathlib import Path
from pprint import pprint   # 리스트·딕셔너리를 줄 맞춰 보기 좋게 찍는다

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI

sys.path.append(str(Path(__file__).resolve().parent.parent))   # 일차 폴더의 utils.py 를 쓴다

from utils import block_text, load_api_key, print_trajectory


DAY_DIR = Path(__file__).resolve().parent.parent    # 일차 폴더(day21). 아래 경로들의 기준점
DATA_DIR = DAY_DIR / "data"      # 실습에 쓰는 CSV·DB 가 있는 곳

load_api_key(DAY_DIR)   # 모델을 부르는 절이 있으므로 키를 맨 앞에서 확인한다

# 파일시스템 서버: 정해 준 폴더의 파일 목록·읽기·쓰기 도구를 내준다.
FILESYSTEM = {
    "command": "npx",                                    # 서버를 띄울 실행기(Node 패키지를 받아 실행한다)
    "args": ["-y",                                       # 설치할지 묻지 않고 진행
             "@modelcontextprotocol/server-filesystem",  # 띄울 서버 패키지 이름
             str(DAY_DIR)],                              # 서버가 볼 수 있는 폴더. 이 밖은 건드리지 못한다
    "transport": "stdio",                                # 내 컴퓨터에 프로세스로 띄우고 표준입출력으로 대화
}


async def main():
    print("\n=== 1. 서버에 붙어 도구 목록 받기 ===")
    # 연결 설정을 넘기면 서버가 뜨고 도구 목록이 돌아온다. "files" 는 서버가 여럿일 때 구분하려고 붙이는 별명이다.
    print("서버를 띄우는 중입니다(첫 실행은 오래 걸립니다)...")
    client = MultiServerMCPClient({"files": FILESYSTEM})

    # session 을 열어 둔 채 그 안에서 도구를 부른다. 서버는 이 블록 동안만 살아 있다.
    async with client.session("files") as session:
        tools = await load_mcp_tools(session)

        # 받은 도구를 '이름(인자): 설명 첫 줄' 형태로 찍어, 우리가 만들지 않은 도구의 명세를 확인한다.
        print(f"도구 {len(tools)}개")
        for tool in tools:
            print(f" - {tool.name}({', '.join(tool.args)}): {tool.description.strip().splitlines()[0][:60]}")

        print("\n=== 2. 도구의 명세 읽기 -- 에이전트가 보는 정보 ===")
        # 에이전트는 도구를 고를 때 이 세 가지만 본다. 우리가 @tool 로 만들 때와 구조가 같다.
        by_name = {tool.name: tool for tool in tools}     # 이름으로 꺼내 쓰려고 딕셔너리로
        listing_tool = by_name["list_directory"]

        print("name       :", listing_tool.name)
        print("description:", listing_tool.description.strip().splitlines()[0])
        print("args       :", listing_tool.args)

        print("\n=== 3. 도구를 직접 호출하기 -- 서버가 준 원래 값 ===")
        # list_directory: 폴더 경로 하나를 받아 그 안의 목록을 돌려주는 도구. MCP 도구는 비동기 전용이라 await 로 부른다.
        result = await listing_tool.ainvoke({"path": str(DATA_DIR)})

        # 돌아온 값을 가공 없이 찍어, MCP 도구의 반환 형태(콘텐츠 블록 리스트)를 눈으로 확인한다.
        pprint(result)

        print("\n=== 4. 그 값에서 사람이 읽을 부분 꺼내기 ===")
        # 블록 리스트에서 첫 블록의 text 키만 꺼내 사람이 읽을 문자열로 만든다.
        print(result[0]["text"])

        print("\n=== 5. 허용된 폴더 밖은 막힌다 ===")
        # 열어 준 폴더 밖을 일부러 부른다. 거부 응답은 문자열로 오기도 해서 [0]["text"] 대신 block_text 로 받는다.
        denied = await listing_tool.ainvoke({"path": str(Path.home())})
        print(block_text(denied))

        print("\n=== 6. 받은 도구를 LangChain 에이전트에 붙이기 ===")
        # 도구를 골라 넘기는 것이 곧 권한 설계다. 읽기 도구 셋만 주면 이 에이전트는 파일을 바꿀 수단이 없다.
        read_only = [by_name[name] for name in ["list_directory", "read_text_file", "get_file_info"]]
        print("넘길 도구:", [tool.name for tool in read_only])

        model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        agent = create_agent(
            model,
            read_only,   # MCP 도구를 그대로 넘긴다 -- 우리가 @tool 로 만든 도구와 같은 자리다
            # 상대경로를 쓰게 한다. 절대경로 속 한글 폴더 이름이 모델을 거치며 모양이 달라져 거부되는 일이 있다.
            system_prompt=(
                "너는 파일을 살펴보는 조사 담당이다. 파일 관련 질문은 반드시 주어진 파일 도구로 확인하고, "
                "내용을 지어내지 않는다. 경로는 data/cvs_sales.csv 처럼 상대경로로 쓴다. "
                "확인한 내용을 근거로 한국어로 간결히 답한다."
            ),
        )

        question = ("data 폴더에 어떤 파일이 있는지 확인하고, cvs_sales.csv 의 첫 3줄을 읽어서 "
                    "이 데이터가 무엇을 담고 있는지 설명해 줘.")
        print("질문:", question, "\n")
        # 도구가 MCP 면 에이전트도 ainvoke 로 부른다. 메시지 기록으로 무엇을 불렀는지 확인한다.
        print_trajectory(await agent.ainvoke({"messages": question}))


# 이 파일을 직접 실행할 때만 main 을 돌린다(다른 파일이 import 해도 실행되지 않게).
if __name__ == "__main__":
    asyncio.run(main())   # 비동기 함수는 이 한 줄로 실행한다(자세한 설명은 부록 노트북)
