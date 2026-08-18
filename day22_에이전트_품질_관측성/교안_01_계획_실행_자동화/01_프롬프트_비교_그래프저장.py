"""실습 01: 같은 질문, 다른 시스템 프롬프트

핵심 목표
    프롬프트 몇 문장 차이로 에이전트의 도구 선택이 갈리는 것을 도구 호출 기록으로 확인한다.

두 버전을 같은 질문으로 한 번씩 돌린다.
    A(말하지 않음): 저장 방법을 아예 적지 않았다. 어느 도구를 쓸지 모델이 알아서 고른다.
    B(갈라 적음): 그림은 code_run-code 안에서 savefig 로, Agg 와 한글 폰트까지 적어 준다.

보는 법
    맨 끝의 비교 표에서 두 파일의 크기와 PNG 서명을 견준다.
    A 는 파일이 생겨도 그림이 아닐 수 있다. 도구의 말이 아니라 파일로 확인하는 것이 이 실습의 요점이다.

실행: 이 파일이 있는 폴더에서  uv run 01_프롬프트_비교_그래프저장.py
준비물: OPENAI_API_KEY(일차 폴더 .env) · npx(Node.js) · uvx(uv)
"""

import asyncio

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain_openai import ChatOpenAI

from 공통 import DAY_DIR, FONT, MODEL_NAME, OUTPUT_DIR, PNG_MAGIC, load_api_key, open_tools
from utils import print_trajectory

load_api_key(DAY_DIR)

# 두 프롬프트가 함께 쓰는 앞부분. 여기까지는 A 와 B 가 똑같다.
COMMON = (
    "너는 데이터 분석 비서다. 표의 조회·집계는 db_read_query 로 SQL 을 실행해 구한다. "
    "숫자를 암산하거나 지어내지 않는다. "
    "코드의 결과에 대한 마지막 줄은 반드시 print 로 출력한다. "
)

# A: 저장 방법을 아예 적지 않았다. 그림을 어느 도구로 만들지 모델이 알아서 고른다.
PROMPT_A = COMMON

# B: 그림과 글을 갈라 적고, 그림에 필요한 것을 코드로 못 박았다. 이 차이가 곧 이 실습의 주제다.
PROMPT_B = COMMON + (
    # 그림을 어느 도구로 만들지 못 박는다. A 에는 이 문장이 없어 모델이 파일 도구로 .png 를 쓰려 든다.
    "그림은 files_write_file 로 만들 수 없다. 그림은 code_run-code 안에서 matplotlib 의 "
    "savefig 로 저장한다. 그래프 코드는 맨 위에 다음 네 줄을 그대로 넣는다.\n"
    # matplotlib 을 직접 import 하는 첫 줄이 없으면 모델이 pyplot 만 불러온 채 matplotlib.use 를
    # 부르다 NameError 로 한 번 실패한 뒤에야 고친다. 네 줄을 통째로 주어 그 한 번을 없앤다.
    "import matplotlib\n"
    "matplotlib.use('Agg')\n"
    "import matplotlib.pyplot as plt\n"
    # 한글 폰트 이름은 OS 마다 다르다. 정해 주지 않으면 모델이 없는 이름을 골라 제목이 네모로 나온다.
    f"plt.rcParams['font.family'] = '{FONT}'\n"
    # 저장했다는 말만 믿을 수 없으니 크기까지 찍게 시킨다.
    "저장한 뒤 os.path.getsize 로 크기를 print 해 0 이 아닌지 확인한다. "
    # 이 서버는 code 만 보내면 인자가 모자란다며 거절한다. 적어 주지 않으면 같은 호출을 되풀이한다.
    "code_run-code 를 부를 때는 code 와 languageId 두 인자를 함께 준다. languageId 는 'python' 이다. "
    "마크다운·텍스트만 files_write_file 로 저장한다. "
    "파일을 저장할 때는 폴더 경로를 적지 않는다. 파일 이름만 적는다."
)

# 두 버전에 똑같이 던지는 질문. 저장 폴더는 프롬프트에 있으니 질문에는 파일 이름만 준다.
def question(name):
    """파일 이름만 갈아 끼운 같은 질문을 돌려준다."""
    return ("invoices 표에서 연도별 매출 합계를 구하고, "
            f"연도별 매출 막대그래프를 '{name}' 이라는 이름으로 저장해 줘.")

CHART_A = OUTPUT_DIR / "비교_A.png"
CHART_B = OUTPUT_DIR / "비교_B.png"


async def run_one(label, system_prompt, chart_path, tools, model):
    """한 버전을 돌리고 도구 호출 기록과 산출물을 찍는다."""
    print(f"\n{'=' * 60}\n[{label}]\n{'=' * 60}")
    agent = create_agent(
        model, tools, system_prompt=system_prompt,
        middleware=[ModelCallLimitMiddleware(run_limit=12, exit_behavior="end")],
    )
    chart_path.unlink(missing_ok=True)     # 지난 실행의 파일을 지우고 시작한다
    print_trajectory(await agent.ainvoke({"messages": question(chart_path.name)}))

    # 도구의 말이 아니라 파일로 확인한다. 0 바이트 파일도 exists() 는 True 다.
    size = chart_path.stat().st_size if chart_path.exists() else 0
    # 확장자가 .png 라고 PNG 인 것이 아니다. 앞 네 바이트(서명)를 봐야 진짜 그림인지 안다.
    is_png = chart_path.exists() and chart_path.read_bytes()[:4] == PNG_MAGIC
    print(f"\n[산출물] {chart_path.name} · 있음 {chart_path.exists()} · 크기 {size} 바이트 · PNG 서명 {is_png}")
    return size, is_png


async def main():
    tools = await open_tools()
    model = ChatOpenAI(model=MODEL_NAME, temperature=0, timeout=60)

    a = await run_one("A. 저장 방법을 적지 않은 프롬프트", PROMPT_A, CHART_A, tools, model)
    b = await run_one("B. 그림 저장을 코드로 못 박은 프롬프트", PROMPT_B, CHART_B, tools, model)

    print(f"\n{'=' * 60}\n[비교]\n{'=' * 60}")
    print(f"A: 크기 {a[0]} 바이트 · PNG {a[1]}")
    print(f"B: 크기 {b[0]} 바이트 · PNG {b[1]}")
    print("\n[보는 법] 두 기록에서 그래프를 어느 도구로 저장했는지 찾아 견주세요.")
    print("  A 는 아무 말이 없으니 모델이 files_write_file 로 .png 를 쓰려다 빈 파일을 남기기 쉽습니다.")
    print("    그 도구는 글자만 쓰는데, 서버는 'Successfully wrote' 라고 답합니다.")
    print("  B 는 code_run-code 안에서 savefig 로 저장하므로 파일이 실제로 남습니다.")
    print("\n[교훈] 도구가 여럿일 때는 '무엇을 어느 도구로' 를 갈라 적어야 합니다.")
    print("       저장 방법을 말하지 않거나 뭉뚱그리면 모델이 엉뚱한 도구를 고릅니다.")
    print(f"       한글 폰트도 마찬가지입니다. 이 판에서는 '{FONT}' 를 프롬프트에 박아 줬습니다.")


# 이 파일을 직접 실행할 때만 main 을 돌린다(다른 파일이 import 해도 실행되지 않게).
if __name__ == "__main__":
    asyncio.run(main())
