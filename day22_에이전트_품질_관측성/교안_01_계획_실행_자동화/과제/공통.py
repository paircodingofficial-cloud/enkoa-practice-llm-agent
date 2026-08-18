"""과제 문제 파일들이 함께 쓰는 설정.

각 문제 파일이 `from 공통 import ...` 로 불러 씁니다. 서버 설정을 문제마다 베껴 두지 않으려고
한곳에 모았습니다. 교안_01 에서 한 줄씩 뜯어본 설정 그대로이고, 이번 과제의 주제는 설정이 아니라
계획·파이프라인·정형화입니다.
"""

import platform
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent          # 과제 폴더. 산출물이 모이는 곳
DAY_DIR = BASE_DIR.parent.parent                    # 일차 폴더(day22). data 와 utils.py 가 있다
DATA_DIR = DAY_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"                    # 그래프·리포트를 모아 둘 곳
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)       # 파일 서버는 없는 폴더를 만들어 주지 않는다

sys.path.append(str(DAY_DIR))   # 일차 폴더의 utils.py 를 쓴다

from utils import child_env, chinook_db_path, load_api_key, quiet_stdio_logs


quiet_stdio_logs()   # 코드 실행 서버가 stdout 에 섞어 보내는 안내문 때문에 나는 긴 경고를 끈다

DB_PATH = chinook_db_path(DATA_DIR)   # data 폴더의 chinook.db 경로. 없으면 그 자리에서 멈춘다
CHILD_ENV = child_env()               # 코드 실행 서버가 python 을 찾게 하는 환경 변수

# DB 조회 서버: 표 목록·스키마·SELECT 를 내준다.
SQLITE = {
    "command": "uvx",
    "args": ["--with", "mcp==1.9.4",      # 이 서버는 최신 mcp 로 띄우면 죽는다. 버전을 고정한다
             "--from", "mcp-server-sqlite",
             "mcp-server-sqlite",
             "--db-path", str(DB_PATH)],
    "transport": "stdio",
}
# 코드 실행 서버: 문자열로 받은 코드를 실행하고 표준 출력을 돌려준다.
# cwd 를 주면 그 서버가 돌리는 코드의 작업 폴더가 정해진다. savefig("그림.png") 가 여기에 떨어진다.
CODE_RUNNER = {
    "command": "npx",
    "args": ["-y", "mcp-server-code-runner"],
    "transport": "stdio",
    "env": CHILD_ENV,
    "cwd": str(OUTPUT_DIR),
}
# 파일시스템 서버: 인자로 준 폴더 안에서만 읽고 쓴다. 그 폴더가 상대경로의 기준이기도 하다.
FILESYSTEM = {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", str(OUTPUT_DIR)],
    "transport": "stdio",
}

# 에이전트에 넘길 도구 이름. 쓰기 도구는 리포트 저장용 하나만 남긴다.
# 넘기지 않은 도구는 모델이 존재조차 모른다. 권한은 말이 아니라 목록으로 준다.
ALLOWED = {"db_read_query", "db_list_tables", "db_describe_table",
           "code_run-code", "files_write_file"}

# 두 서버가 같은 output 폴더에서 돌므로 에이전트에게는 파일 이름만 시킨다.
# 긴 경로를 프롬프트에 넣으면 모델이 그 경로를 다시 타이핑하다 오타를 내고,
# 코드 실행 서버는 그 오타를 걸러 주지 않아 엉뚱한 폴더에 조용히 저장된다.
CHART_NAME = "장르별_매출.png"
REPORT_NAME = "장르별_리포트.md"
CHART_PATH = OUTPUT_DIR / CHART_NAME       # 우리가 확인할 때 쓰는 절대경로
REPORT_PATH = OUTPUT_DIR / REPORT_NAME
METRICS_PATH = OUTPUT_DIR / "metrics.json"

# 운영체제마다 있는 한글 폰트 이름. 그래프에 한글이 네모로 깨지지 않게 에이전트에게 알려 준다.
FONT = {"Windows": "Malgun Gothic", "Darwin": "AppleGothic"}.get(platform.system(), "NanumGothic")

# 에이전트에 공통으로 넣는 지시. 교안_01 의 SYSTEM_BASE 에 도구 인자 규칙 한 문장을 더한 것이다.
# (그 한 문장이 없으면 모델이 languageId 를 빠뜨린 채 같은 호출을 되풀이하다 상한에서 끝나는 일이 있다.)
SYSTEM_BASE = (
    "너는 데이터 분석 비서다. 표의 조회·집계는 db_read_query 로 SQL 을 실행해 구하고, "
    "그 결과를 가공하는 계산과 그래프는 code_run-code 로 한다. 숫자를 암산하거나 지어내지 않는다. "
    "코드의 마지막 줄은 반드시 print 로 출력한다. 값만 적은 줄은 아무것도 돌려주지 않는다. "
    "결과가 비어 있으면 print 를 빠뜨린 것이니 print 를 넣어 다시 실행한다. "
    "경고(Stderr)만 돌아오면 이 서버가 표준 출력을 버린 것이다. 코드 맨 위에서 "
    "warnings.filterwarnings('ignore') 로 경고를 끄고 다시 실행한다. "
    "같은 코드를 두 번 보내지 않는다. "
    "code_run-code 를 부를 때는 code 와 languageId 두 인자를 함께 준다. languageId 는 'python' 이다. "
    "code_run-code 는 한 번에 하나씩만 부른다. 이 서버는 모든 코드를 같은 임시 파일에 쓰므로 "
    "동시에 두 번 부르면 서로의 코드를 덮어써 실패한다. "
    "SQL 을 처음 쓰기 전에 db_list_tables 로 표 목록을 보고, db_describe_table 로 쓸 표의 열 이름을 "
    "반드시 확인한다. 열 이름을 짐작해서 쓰지 않는다. 이 DB 는 표 이름이 invoices 처럼 소문자이고 "
    "열 이름은 InvoiceDate 처럼 대문자로 시작해서, 짐작하면 대개 틀린다. "
    "매출을 표 여럿에 걸쳐 구할 때는 invoice_items 의 UnitPrice * Quantity 를 더한다. "
    "invoices 의 Total 을 invoice_items 와 이어 붙여 더하면 한 청구서의 금액이 줄 수만큼 "
    "거듭 세어져 값이 부풀려진다. "
    "표 조회는 반드시 db_read_query 로 한다. code_run-code 안에서 sqlite3 로 DB 에 직접 붙지 않는다. "
    "그 서버는 DB 파일이 있는 자리를 모른다. "
    "그림은 files_write_file 로 만들 수 없다. 그림은 code_run-code 안에서 matplotlib 의 "
    "savefig 로 저장하고, 저장한 뒤 os.path.getsize 로 크기를 print 해 0 이 아닌지 확인한다. "
    "그래프 코드는 맨 위에 다음 네 줄을 그대로 넣는다. 창을 띄우지 않고, 한글이 네모로 깨지지 않게 하려는 것이다.\n"
    # matplotlib 을 직접 import 하는 첫 줄이 없으면 모델이 pyplot 만 불러온 채 matplotlib.use 를
    # 부르다 NameError 로 한 번 실패한 뒤에야 고친다. 네 줄을 통째로 주어 그 한 번을 없앤다.
    "import matplotlib\n"
    "matplotlib.use('Agg')\n"
    "import matplotlib.pyplot as plt\n"
    f"plt.rcParams['font.family'] = '{FONT}'\n"
    "마크다운·텍스트만 files_write_file 로 저장한다. "
    "파일을 저장할 때는 폴더 경로를 적지 않는다. 파일 이름만 적는다. "
    "두 도구 모두 저장 폴더에서 실행되므로 이름만 적으면 그 폴더에 저장된다."
)

# 계획을 세우게 하는 한 문장. SYSTEM_BASE 뒤에 이어 붙여 쓴다.
PLAN_RULE = (" 요청을 받으면 무엇을 하든 첫 도구 호출은 반드시 write_todos 여야 한다. "
             "할 일을 단계로 나눠 계획을 세운 뒤 하나씩 처리한다. 한 단계를 끝내면 곧바로 "
             "write_todos 를 다시 불러 그 항목을 completed 로 바꾼다. 마지막에는 모든 항목이 completed 여야 한다.")
