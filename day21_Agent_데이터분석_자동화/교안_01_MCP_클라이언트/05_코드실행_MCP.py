"""교안 01-5: 코드 실행 MCP 서버 붙이기

핵심 목표
    코드 실행 서버를 붙여, 모델이 암산 대신 코드를 돌려 검증 가능한 값으로 답하게 만든다.

학습 순서
    1) 코드 실행 서버(mcp-server-code-runner) 연결과 run-code 도구
    2) 코드를 문자열로 넘겨 실행하고 출력 받기
    3) print 가 없으면 아무것도 돌아오지 않는 이유
    4) 여러 줄 코드 보내기
    5) 모델이 스스로 코드를 짜서 계산하게 하기

쓰는 MCP 서버와 공식 문서
    코드 실행 서버 mcp-server-code-runner
        https://github.com/formulahendry/mcp-server-code-runner

실행: 이 파일이 있는 폴더에서  uv run 05_코드실행_MCP.py

에이전트를 만드는 절부터 OPENAI_API_KEY 가 필요합니다(일차 폴더의 .env).
"""

import asyncio
import sys
from pathlib import Path
from pprint import pprint   # 리스트·딕셔너리를 줄 맞춰 보기 좋게 찍는다

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI

sys.path.append(str(Path(__file__).resolve().parent.parent))   # 일차 폴더의 utils.py 를 쓴다

from utils import child_env, load_api_key, print_trajectory, quiet_stdio_logs


quiet_stdio_logs()   # 코드 실행 서버가 stdout 에 섞어 보내는 안내문 때문에 나는 긴 경고를 끈다

DAY_DIR = Path(__file__).resolve().parent.parent    # 일차 폴더(day21). 아래 경로들의 기준점

load_api_key(DAY_DIR)   # 모델을 부르는 파일이라 키를 맨 앞에서 확인한다

CHILD_ENV = child_env()   # 코드 실행 서버가 python 을 찾을 수 있게 PATH 를 맞춰 넘긴다

# 코드 실행 서버: 문자열로 받은 코드를 실행하고 표준 출력을 돌려준다.
CODE_RUNNER = {
    "command": "npx",                          # Node 패키지 실행기
    "args": ["-y", "mcp-server-code-runner"],  # 묻지 않고 진행 + 띄울 서버 패키지 이름
    "transport": "stdio",                      # 내 컴퓨터에 프로세스로 띄운다
    "env": CHILD_ENV,                          # 위에서 만든 환경 변수(서버가 python 을 찾게 한다)
}

# 에이전트에게 시킬 계산 -- 사람이 암산하기 어려운 값이라 "코드로 계산했는지"가 눈에 보인다.
sales = [318000, 274500, 391200, 288900, 350100, 412700, 299800]


async def main():
    print("\n=== 1. 코드 실행 서버에 붙기 ===")
    print("서버를 띄우는 중입니다(첫 실행은 오래 걸립니다)...")
    client = MultiServerMCPClient({"code": CODE_RUNNER})

    async with client.session("code") as session:
        tools = await load_mcp_tools(session)
        # 도구 이름은 서버가 정한다. 여기서는 하이픈이 든 run-code 라, 점 표기 대신 딕셔너리로 꺼낸다.
        run_code = {tool.name: tool for tool in tools}["run-code"]

        # run-code: 코드 문자열과 languageId 를 받아 실행하고 표준 출력을 돌려주는 도구.
        print(f"도구 {len(tools)}개")
        for tool in tools:
            print(f" - {tool.name}({', '.join(tool.args)}): {tool.description.strip().splitlines()[0][:60]}")

        print("\n=== 2. 코드를 넘겨 실행하기 ===")
        # languageId 로 어떤 언어인지 알려 준다. 서버가 그 언어의 실행기를 찾아 돌린다.
        snippet = "print(sum([1, 2, 3, 4, 5]))"

        print("보낸 코드 :", snippet)
        print("받은 결과 :", (await run_code.ainvoke({"code": snippet, "languageId": "python"}))[0]["text"])

        print("\n=== 3. 출력하지 않으면 아무것도 돌아오지 않는다 ===")
        # 같은 계산을 print 없이 한 번, print 를 붙여 한 번 보내 두 반환값을 나란히 본다.
        # 이 서버가 돌려주는 것은 표준 출력뿐이라는 사실을 확인하는 자리다.
        pprint(await run_code.ainvoke({"code": "1 + 1", "languageId": "python"}))
        pprint(await run_code.ainvoke({"code": "print(1 + 1)", "languageId": "python"}))

        print("\n=== 4. 여러 줄 코드도 그대로 보낸다 ===")
        # 줄바꿈(\n)을 이어 붙여 여러 줄짜리 코드 문자열을 만든다. 파일로 저장할 필요가 없다.
        stats_code = (
            "import statistics\n"
            f"sales = {sales}\n"
            "print('평균:', round(statistics.mean(sales), 1))\n"
            "print('표준편차:', round(statistics.pstdev(sales), 1))"
        )

        print(stats_code)
        print("-" * 40)
        print((await run_code.ainvoke({"code": stats_code, "languageId": "python"}))[0]["text"])

        print("\n=== 5. 에이전트에 붙이기 -- 모델이 스스로 코드를 짠다 ===")
        # timeout 을 준다. 기본값은 요청 하나를 10분까지 기다리고 두 번 더 재시도해서,
        # 응답이 늦거나 분당 한도에 걸리면 화면만 보고는 멈춘 것과 구별되지 않는다.
        model = ChatOpenAI(model="gpt-4o-mini", temperature=0, timeout=60)

        agent = create_agent(
            model,
            tools,                      # 서버에서 받은 도구를 그대로 붙인다
            # 이 서버의 성질을 프롬프트에 미리 적어 둔다. 모델은 결과만 보고는 왜 비었는지 알 수 없어,
            # 안 적어 두면 이유를 모른 채 같은 코드를 계속 다시 보낸다(화면이 멈춘 것처럼 보인다).
            system_prompt=(
                "너는 데이터 분석 도우미다. 수치 계산은 반드시 코드 실행 도구로 계산한 뒤 그 결과로 답한다. "
                "코드의 결과에 대한 마지막 줄은 반드시 print 로 출력한다."
                "결과가 비어 있으면 print 를 빠뜨린 것이니 print 를 넣어 다시 실행한다. "
            ),
            # ModelCallLimitMiddleware 로 모델 호출 횟수에 상한을 둔다. 반복에 빠져도 상한에서 스스로
            # 끝나므로(exit_behavior="end") 예외 없이 여태 기록을 그대로 돌려준다.
            middleware=[ModelCallLimitMiddleware(run_limit=8, exit_behavior="end")],
        )

        question = (
            f"다음 7일치 매출 {sales} 의 평균과 표준편차(모표준편차)를 구하고, "
            "평균보다 큰 날이 며칠인지 알려 줘. 암산하지 말고 반드시 코드를 실행해서 계산해."
        )
        print("질문:", question, "\n")

        print_trajectory(await agent.ainvoke({"messages": question}))


# 이 파일을 직접 실행할 때만 main 을 돌린다(다른 파일이 import 해도 실행되지 않게).
if __name__ == "__main__":
    asyncio.run(main())
