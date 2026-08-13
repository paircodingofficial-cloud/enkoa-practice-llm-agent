"""과제 문제 파일들이 함께 쓰는 설정.

각 문제 파일이 `from 공통 import ...` 로 불러 씁니다. 서버 설정을 문제마다 베껴 두지 않으려고
한곳에 모았습니다. 문제 3 의 Context7 설정만 여기에 없습니다. 그 설정을 직접 만드는 것이 문제입니다.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))   # 일차 폴더의 utils.py 를 쓴다

from langchain_core.tools import tool

from utils import child_env, load_api_key, quiet_stdio_logs


quiet_stdio_logs()   # 코드 실행 서버가 stdout 에 섞어 보내는 안내문 때문에 나는 긴 경고를 끈다

DAY_DIR = Path(__file__).resolve().parent.parent.parent   # 일차 폴더(day21)
DATA_DIR = DAY_DIR / "data"       # 실습에 쓰는 CSV·DB 가 있는 곳
OUTPUT_DIR = DAY_DIR / "output"   # 산출물을 모아 둘 곳

CHAIN_PATH = OUTPUT_DIR / "basic_chain.py"   # 문제 4 에서 저장할 체인 코드 파일

CHILD_ENV = child_env()   # 코드 실행 서버가 python 을 찾을 수 있게 PATH 를 맞춰 넘긴다

# 파일시스템 서버: 정해 준 폴더의 파일 목록·읽기·쓰기 도구를 내준다.
FILESYSTEM = {
    "command": "npx",                                    # 서버를 띄울 실행기(Node 패키지를 받아 실행한다)
    "args": ["-y",                                       # 설치할지 묻지 않고 진행
             "@modelcontextprotocol/server-filesystem",  # 띄울 서버 패키지 이름
             str(DAY_DIR)],                              # 서버가 볼 수 있는 폴더. 이 밖은 건드리지 못한다
    "transport": "stdio",                                # 내 컴퓨터에 프로세스로 띄우고 표준입출력으로 대화
}
# 코드 실행 서버: 문자열로 받은 코드를 실행하고 표준 출력을 돌려준다.
CODE_RUNNER = {
    "command": "npx",                          # Node 패키지 실행기
    "args": ["-y", "mcp-server-code-runner"],  # 묻지 않고 진행 + 띄울 서버 패키지 이름
    "transport": "stdio",
    "env": CHILD_ENV,                          # 위에서 만든 환경 변수(서버가 python 을 찾게 한다)
}


# 우리 규칙에 대한 우리 도구 -- 공식 문서에는 없고 우리만 아는 값이다(문제 4 에서 쓴다).
@tool
def team_llm_rule() -> str:
    """우리 팀이 쓰기로 정한 모델 이름과 온도를 돌려준다."""
    return "모델 이름은 gpt-4o-mini, temperature 는 0 으로 고정한다."
