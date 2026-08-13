# MCP 클라이언트 실습: 남이 만든 도구를 에이전트에 붙이기

**서버 제작은 다루지 않습니다.** 이미 공개된 MCP 서버에 **붙여 쓰는 쪽**(클라이언트)만 배웁니다.

개념 노트북 **`교안_01_MCP_개념.ipynb`** 가 이 폴더에 함께 있습니다. 그것부터 읽고 오세요.

| 파일 | 무엇 | 형식 |
|---|---|---|
| `01_파일시스템_MCP.py` | 파일시스템 서버에 붙어 도구 목록·명세·직접 호출, 에이전트에 붙이기 | 실습 |
| `02_웹검색_MCP.py` | 웹 검색 서버 + 에이전트가 스스로 검색해 답하기 | 실습 |
| `03_브라우저조작_Playwright.py` | 브라우저 서버로 페이지를 열고 화면 구조를 읽기 | 실습 |
| `04_SQLite_MCP.py` | DB 서버 + 에이전트가 스키마를 보고 스스로 SELECT 쓰기 | 실습 |
| `05_코드실행_MCP.py` | 코드 실행 서버 + 모델이 코드를 짜서 계산하기 | 실습 |
| `06_종합_데이터분석_자동화.py` | 종합: 서버 3개를 한꺼번에(접두사) · DB 조회 → 코드 계산·그래프 → 파일 저장 | 실습 |
| `../utils.py` | 일차 폴더에 있는 공용 도우미(키 확인·환경 변수·반환값 문자열 뽑기·도구 호출 기록 출력). 교안_01·교안_02·과제가 함께 쓴다 | 제공 |
| `과제/문제1~4_*.py` | 과제 4문. 문제마다 파일 하나이고 자가채점이 붙어 있다 | 과제 |
| `과제/공통.py` | 과제 문제들이 함께 쓰는 서버 설정·경로·우리 도구 | 제공 |
| `과제/정답/` | 과제 정답 | 강사용 |

> **`async`·`await` 가 처음이면** 일차 폴더의 **`부록_동기_비동기_기초.ipynb`** 를 먼저 열어 보세요.

## 실행 방법

이 폴더에서 파일 이름만 주면 됩니다. `uv` 가 알아서 `실습자료` 의 가상환경을 찾아 씁니다.

```bash
uv run 01_파일시스템_MCP.py
```

01 → 02 → 03 → 04 → 05 → 06 순서로 실행하고, 마지막에 `과제/` 의 문제 1~4 를 풉니다.
**같은 이름의 `.ipynb` 판이 함께 있습니다.** 내용은 같고 노트북에 맞게 고친 부분만 다릅니다(설명과 그림이 더 자세하고, 따라하기가 셀로 나뉘어 있습니다). 편한 쪽으로 실습하세요.
각 파일은 `async def main()` 하나와 맨 아래 `asyncio.run(main())` 로 되어 있습니다.

> **`.py` 와 `.ipynb` 의 차이**: MCP 의 `stdio` 방식은 서버를 자식 프로세스로 띄웁니다.
> **맥·리눅스 주피터에서는 그대로 됩니다**(주피터 커널이 stdio 서버를 자식 프로세스로 띄울 수 있습니다).
> 다만 **윈도우 주피터 커널은 자식 프로세스를 띄우지 못해** 그 자리에서 실패할 수 있습니다. 윈도우라면 `.py` 판으로 실습하세요.
> 노트북 판은 `.py` 판에서 세 곳이 다릅니다: `asyncio.run(...)` 대신 **셀에서 바로 `await`**,
> `__file__` 대신 **`Path.cwd()`**, `async with client.session(...)` 대신 **`await client.get_tools(...)`**
> (03 번만 예외로 세션을 직접 열고 닫습니다).

## 필요한 것

```bash
uv add langchain langchain-openai langchain-mcp-adapters mcp pandas matplotlib python-dotenv
npx playwright install chromium     # 03 번 브라우저 실습에만 필요합니다(약 150MB)
```

| 준비물 | 확인 | 없으면 |
|---|---|---|
| `OPENAI_API_KEY` | 일차 폴더의 `.env` | `cp .env.example .env` 후 키 입력 |
| **Node.js**(`npx`) | `npx -v` | https://nodejs.org (파일시스템·코드실행·브라우저 서버가 씁니다) |
| **uv**(`uvx`) | `uvx --version` | https://docs.astral.sh/uv/ (검색·DB 서버가 씁니다) |
| 크로미움 | `npx playwright install chromium` | 03 번 파일에서만 필요 |
| 인터넷 | - | 서버 패키지 내려받기·검색·페이지 열기에 필요 |

첫 실행은 서버 패키지를 내려받느라 **수십 초** 걸립니다. 두 번째부터는 빠릅니다.

## 붙여 보는 서버 (모두 API 키 불필요)

| 서버 | 실행 | 도구 | 전송 | 공식 문서 |
|---|---|---|---|---|
| 파일시스템 | `npx @modelcontextprotocol/server-filesystem <폴더>` | `list_directory`·`read_text_file` 등 14개 | stdio | https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem |
| 웹 검색 | `uvx duckduckgo-mcp-server` | `search`·`fetch_content` | stdio | https://github.com/nickclyde/duckduckgo-mcp-server |
| 코드 실행 | `npx mcp-server-code-runner` | `run-code` | stdio | https://github.com/formulahendry/mcp-server-code-runner |
| 브라우저 조작 | `npx @playwright/mcp` | `browser_navigate`·`browser_snapshot`·`browser_click` 등 20여 개 | stdio | https://github.com/microsoft/playwright-mcp |
| DB 조회 | `uvx --from mcp-server-sqlite mcp-server-sqlite --db-path <파일>` | `list_tables`·`describe_table`·`read_query` 등 6개 | stdio | https://pypi.org/project/mcp-server-sqlite/ |
| 문서 조회(과제) | `https://mcp.context7.com/mcp` | `resolve-library-id`·`query-docs` | HTTP(원격) | https://github.com/upstash/context7 |

MCP 규격 자체의 공식 문서는 https://modelcontextprotocol.io/docs/getting-started/intro 입니다.
각 실습 파일 맨 위 설명에도 그 파일이 쓰는 서버의 문서 주소를 적어 두었습니다.

파일시스템 서버는 **인자로 준 폴더(day21) 안에서만** 동작합니다. 권한을 좁히는 자리입니다.

## 코드에서 반복되는 형태

파일마다 아래 네 줄이 그대로 들어 있습니다.

```python
from utils import load_api_key, print_trajectory          # 일차 폴더의 utils.py 에 모아 둔 도우미

client = MultiServerMCPClient({"search": WEB_SEARCH})   # 별명을 붙여 클라이언트를 만들고
tools = await client.get_tools()                        # 서버에 붙어 도구 목록을 받고
by_name = {tool.name: tool for tool in tools}           # 이름으로 꺼내 쓸 수 있게 정리하고
result = await by_name["search"].ainvoke({"query": "MCP", "max_results": 3})
print(result[0]["text"])       # MCP 결과는 콘텐츠 블록 리스트다
```

- 키 확인(`load_api_key`)·코드 실행 서버용 환경 변수(`child_env`)·도구 호출 기록 출력(`print_trajectory`)처럼
  파일마다 똑같던 코드는 일차 폴더의 **`utils.py`** 한곳에 모아 두고 `from utils import ...` 로 불러 씁니다.
  일차 폴더는 교안_01 밖이라, 부르는 파일 맨 앞에서 `sys.path.append(...)` 한 줄로 검색 경로에 넣어 줍니다.
  그 안에 왜 필요한 코드인지 적어 두었으니 실습 중에 한 번 열어 보세요.

- MCP 반환값은 문자열이 아니라 **콘텐츠 블록 리스트**(`[{'type': 'text', 'text': ...}]`)입니다.
  그래서 사람이 읽을 값은 `result[0]["text"]` 로 꺼냅니다. 구조를 눈으로 보고 싶으면 `pprint(result)` 를 씁니다.
- MCP 도구는 `await tool.ainvoke(...)` 로만 부릅니다. 동기 `invoke` 는 `NotImplementedError` 입니다.
- 브라우저 서버(05)만 `async with client.session("web")` 으로 세션을 열어 둡니다. 열어 둔 페이지가
  다음 호출까지 남아 있어야 `navigate → snapshot → click` 이 이어지기 때문입니다.

## 알아 두면 좋은 것

- 서버가 남기는 로그가 실습 출력 사이에 섞일 수 있습니다. 서버는 우리가 띄운 자식 프로세스라 화면을 같이 씁니다.
- **`RateLimitError: ... tokens per min (TPM)`** 이 뜨면 분당 토큰 한도에 걸린 것입니다. 도구를 많이 붙일수록
  도구 설명이 매 요청에 실려 토큰이 커집니다. **1분쯤 기다렸다가 다시 실행**하면 됩니다.
  03 번 파일에서 도구를 골라 넘기는 것도 같은 이유입니다.
- 코드 실행 서버는 **표준 출력만** 돌려줍니다. 값만 적은 코드(`ratio`)는 빈 결과가 오므로 `print(ratio)` 로
  출력해야 합니다. 에이전트에게도 시스템 프롬프트로 그렇게 지시해 두었습니다.

## 과제

`과제/` 폴더의 문제 파일을 번호 순서로 풉니다. 파일마다 `# [자가채점]` 블록이 답을 검사하고,
통과하면 "문제 N 통과" 가 찍힙니다. 아직 안 푼 문제에서 멈추는 것이 정상입니다.
