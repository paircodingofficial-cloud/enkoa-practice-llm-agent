"""교안 01-3: 브라우저를 조작하는 MCP 서버 붙이기 (Playwright)

핵심 목표
    브라우저 서버로 무한 스크롤 페이지를 실제로 움직여, 주소만으로는 닿지 않는 이미지를 모은다.

학습 순서
    1) Playwright 서버 연결과 도구 20여 개
    2) 무한 스크롤 이미지 페이지 열기(browser_navigate)와 화면 구조 스냅샷(browser_snapshot)
       -- 크롬 창이 실제로 떠서 움직이는 것을 눈으로 본다(--headless 를 넣지 않았다)
    3) 스크롤하며 이미지 모으기(browser_press_key·browser_wait_for·browser_evaluate)
    4) 필요한 도구만 골라 붙인 에이전트가 스스로 스크롤해 이미지 모으기
       (본문은 이 네 가지를 1~5절로 나눠 진행한다: 연결·열기·읽기·모으기·에이전트)

쓰는 MCP 서버와 공식 문서
    브라우저 조작 서버 @playwright/mcp
        https://github.com/microsoft/playwright-mcp

준비물
    브라우저 실행 파일이 한 번은 설치돼 있어야 합니다(실습자료 폴더에서, 약 150MB).
        npx playwright install chromium

실행: 이 파일이 있는 폴더에서  uv run 03_브라우저조작_Playwright.py

에이전트를 만드는 절부터 OPENAI_API_KEY 가 필요합니다(일차 폴더의 .env).
"""

import asyncio
import sys
from pathlib import Path

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI

sys.path.append(str(Path(__file__).resolve().parent.parent))   # 일차 폴더의 utils.py 를 쓴다

from utils import load_api_key, print_trajectory, result_value


DAY_DIR = Path(__file__).resolve().parent.parent    # 일차 폴더(day21). 아래 경로들의 기준점
OUTPUT_DIR = DAY_DIR / "output"  # 브라우저 서버가 남기는 파일을 모아 둘 곳

load_api_key(DAY_DIR)   # 모델을 부르는 파일이라 키를 맨 앞에서 확인한다

# 실습에 쓸 페이지. 스크래핑 연습용으로 공개된 무한 스크롤 페이지다.
# 화면을 내릴 때마다 상품 이미지가 12장씩 더 붙는다.
SITE = "https://www.scrapingcourse.com/infinite-scrolling"

# 브라우저 조작 서버: 페이지를 열고 화면 구조를 읽고 클릭·입력하는 도구를 내준다.
PLAYWRIGHT = {
    "command": "npx",                              # Node 패키지 실행기
    "args": ["-y", "@playwright/mcp@latest",       # 띄울 서버 패키지 이름
             # "--headless",                       # 이 줄을 살리면 창 없이 돈다(서버·자동화 환경용)
             "--isolated",                         # 쿠키·로그인을 남기지 않는 임시 프로필로 띄운다
             "--output-dir", str(OUTPUT_DIR)],     # 스냅샷·스크린샷 파일을 남길 폴더
    "transport": "stdio",                          # 내 컴퓨터에 프로세스로 띄운다
}


async def main():
    print("\n=== 1. 브라우저 서버에 붙기 ===")
    print("서버를 띄우는 중입니다(첫 실행은 오래 걸립니다)...")
    client = MultiServerMCPClient({"web": PLAYWRIGHT})

    # 이 서버는 상태를 가진다. 열어 둔 페이지가 남아야 navigate -> snapshot 이 이어지므로 session 을 연 채로 처리한다.
    async with client.session("web") as session:
        tools = await load_mcp_tools(session)
        by_name = {tool.name: tool for tool in tools}

        # 도구 이름을 훑어 둔다. 뒤에서 이 중 필요한 것만 골라 에이전트에 넘긴다.
        print(f"도구 {len(tools)}개")
        print(" ", ", ".join(sorted(by_name)))

        print("\n=== 2. 페이지 열기 ===")
        # browser_navigate: 주소 하나를 받아 그 페이지를 여는 도구.
        print((await by_name["browser_navigate"].ainvoke({"url": SITE}))[0]["text"])

        print("\n=== 3. 화면을 스냅샷으로 읽기 ===")
        # browser_snapshot: 열린 화면을 접근성 트리 텍스트로 받아 오는 도구. ref=e12 표식이 클릭 대상의 주소가 된다.
        snapshot = (await by_name["browser_snapshot"].ainvoke({}))[0]["text"]
        print("스냅샷 길이:", len(snapshot), "자")
        print(snapshot[:800])

        print("\n=== 4. 스크롤하며 이미지 모으기 ===")
        # 페이지 안에서 실행할 자바스크립트. 화살표 함수를 문자열로 넘기면 서버가 페이지에서 실행해 값을 돌려준다.
        COUNT_IMAGES = "() => document.querySelectorAll('img').length"

        # browser_evaluate: 준 자바스크립트를 열린 페이지에서 실행해 값을 돌려주는 도구.
        print("처음 이미지 수:", result_value(await by_name["browser_evaluate"].ainvoke({"function": COUNT_IMAGES})))

        for step in range(1, 4):
            # browser_press_key: 사람이 키보드를 누르듯 키를 보내는 도구. End 는 화면을 맨 아래로 내린다.
            await by_name["browser_press_key"].ainvoke({"key": "End"})
            # browser_wait_for: 정해진 시간만큼 기다리는 도구. 새 이미지를 받아 그릴 틈을 준다.
            await by_name["browser_wait_for"].ainvoke({"time": 2})
            counted = result_value(await by_name["browser_evaluate"].ainvoke({"function": COUNT_IMAGES}))
            print(f"{step}번째 스크롤 뒤 이미지 수:", counted)

        # 같은 도구에 다른 자바스크립트를 넘기면 되는 일이 달라진다. 이번엔 개수가 아니라 주소를 꺼낸다.
        IMAGE_SOURCES = "() => Array.from(document.querySelectorAll('img')).map(img => img.src)"

        sources = result_value(await by_name["browser_evaluate"].ainvoke({"function": IMAGE_SOURCES}))
        print(sources[:600])

        print("\n=== 5. 에이전트에 붙이기 -- 필요한 도구만 골라서 ===")
        # 도구를 다 넘기면 모델이 설명을 전부 읽어야 해서 비용이 커지고 선택도 흔들린다. 필요한 것만 고른다.
        needed = ["browser_navigate", "browser_press_key", "browser_wait_for", "browser_evaluate"]
        picked = [by_name[name] for name in needed]
        print("에이전트에 넘길 도구:", needed)

        model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        agent = create_agent(
            model,
            picked,
            system_prompt=(
                "너는 웹 페이지에서 자료를 모으는 담당이다. "
                "먼저 browser_navigate 로 페이지를 열고, browser_press_key 로 End 키를 눌러 화면을 내린 뒤 "
                "browser_wait_for 로 2초쯤 기다려 새 내용이 그려질 시간을 준다. "
                "화면에 실제로 있는 값만 쓰고, 주소를 지어내지 않는다. "
                "이미지 주소는 browser_evaluate 에 "
                "\"() => Array.from(document.querySelectorAll('img')).map(img => img.src)\" 를 넘겨 확인한다."
            ),
        )

        # 세는 시점을 문장에 못 박는다. "처음 이미지 수" 만 적으면 모델이 세어 보지 않고 지어낸다.
        question = (
            f"{SITE} 를 열고, 스크롤하기 전에 먼저 이미지 수를 세어 둬. "
            "그다음 화면을 끝까지 세 번 내리고, 내릴 때마다 2초씩 기다린 뒤 이미지 수를 다시 세어 줘. "
            "마지막에 처음 수와 마지막 수, 그리고 상품 이미지 주소 5개를 목록으로 보여 줘. "
            "두 수 모두 browser_evaluate 로 실제로 센 값이어야 한다."
        )
        print("질문:", question, "\n")
        print_trajectory(await agent.ainvoke({"messages": question}))


# 이 파일을 직접 실행할 때만 main 을 돌린다(다른 파일이 import 해도 실행되지 않게).
if __name__ == "__main__":
    asyncio.run(main())
