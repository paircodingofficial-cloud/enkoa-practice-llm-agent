"""교안 01 실습 파일들이 함께 쓰는 설정.

각 실습 파일이 `from 공통 import ...` 로 불러 씁니다. 서버 설정과 경로를 파일마다 베껴 두면
한쪽만 고쳤을 때 아무 에러 없이 조용히 갈라지므로 한곳에 모았습니다.

다만 **모델에 보내는 프롬프트는 여기에 두지 않습니다.** 실습 파일을 열었을 때 무엇이 모델로 나가는지
그 자리에서 읽혀야 하기 때문입니다. 프롬프트는 각 실습 파일 안에 그대로 적혀 있습니다.

이론 설명(미들웨어가 무엇인지, 훅 여섯 자리, before/after 와 wrap 의 차이)은 같은 폴더의 노트북
`교안_01_계획_실행_자동화.ipynb` 에 그림과 함께 있습니다. 이 `.py` 들은 그 이론을 실행으로 확인하는 판입니다.
"""

import platform
import sys
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient

BASE_DIR = Path(__file__).resolve().parent          # 교안_01 폴더
DAY_DIR = BASE_DIR.parent                           # 일차 폴더(day22). data 와 utils.py 가 있다
DATA_DIR = DAY_DIR / "data"
OUTPUT_DIR = DAY_DIR / "output"                     # 그래프·리포트가 모이는 곳
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)       # 파일 서버는 없는 폴더를 만들어 주지 않는다

sys.path.append(str(DAY_DIR))   # 일차 폴더의 utils.py 를 쓴다

# load_api_key 는 여기서 쓰지 않고 각 실습 파일이 `from 공통 import load_api_key` 로 가져다 쓴다
from utils import child_env, chinook_db_path, load_api_key, quiet_stdio_logs  # noqa: E402,F401

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
# 코드 실행 서버: 계산과 그래프를 맡는다. cwd 가 상대경로의 기준이라 savefig("그림.png") 가 거기에 떨어진다.
CODE_RUNNER = {
    "command": "npx",
    "args": ["-y", "mcp-server-code-runner"],
    "transport": "stdio",
    "env": CHILD_ENV,
    "cwd": str(OUTPUT_DIR),
}
# 파일 서버: 열어 준 폴더가 곧 쓰기 허용 범위이자 상대경로의 기준이다.
FILESYSTEM = {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", str(OUTPUT_DIR)],
    "transport": "stdio",
}

# 한글 폰트 이름은 OS 마다 다르다. "한글 폰트를 써라" 라고만 하면 모델이 없는 이름을 골라
# 제목이 네모(□□□)로 나온다. 여기서 정해 프롬프트에 넣어 준다.
FONT = {"Windows": "Malgun Gothic", "Darwin": "AppleGothic"}.get(platform.system(), "NanumGothic")

# 에이전트에 넘길 도구. 쓰기 도구는 리포트 저장용 하나만 남긴다.
# 넘기지 않은 도구는 모델이 존재조차 모른다. 권한은 말이 아니라 목록으로 준다.
ALLOWED = {"db_read_query", "db_list_tables", "db_describe_table",
           "code_run-code", "files_write_file"}

PNG_MAGIC = b"\x89PNG"   # 진짜 PNG 파일은 이 네 바이트로 시작한다

MODEL_NAME = "gpt-4o-mini"


async def open_tools(*servers):
    """고른 MCP 서버에 붙어 허용 도구(ALLOWED)만 골라 돌려준다.

    servers 를 비우면 세 개를 모두 띄운다. DB 만 필요하면 open_tools("db") 로 부른다.
    """
    conf = {"db": SQLITE, "code": CODE_RUNNER, "files": FILESYSTEM}
    picked = {name: conf[name] for name in (servers or conf)}
    print(f"MCP 서버 {len(picked)}개를 띄우는 중입니다(첫 실행은 오래 걸립니다)...")
    # tool_name_prefix=True 는 db_·code_·files_ 접두사를 붙인다. 서버끼리 도구 이름이 겹쳐도 충돌하지 않는다
    client = MultiServerMCPClient(picked, tool_name_prefix=True)
    tools = [t for t in await client.get_tools() if t.name in ALLOWED]
    print("에이전트에 쓸 도구:", [t.name for t in tools])
    return tools


def report_file(path):
    """파일이 정말 저장됐는지 크기까지 찍는다(0 바이트 파일도 exists() 는 True 다)."""
    size = path.stat().st_size if path.exists() else 0
    print(f"{path.name:24} 있음={path.exists()} 크기={size}바이트")
    return size
