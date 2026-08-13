"""이 일차의 실습 파일들이 함께 쓰는 도우미 모음.

교안_01·교안_02·과제가 모두 `from utils import ...` 로 불러 씁니다.
일차 폴더에 있으므로, 부르는 쪽에서 이 폴더를 모듈 검색 경로에 한 줄 넣어 줍니다.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage


def quiet_stdio_logs() -> None:
    """MCP 클라이언트가 남기는 JSONRPC 파싱 실패 로그를 끈다.

    코드 실행 서버가 stdout 에 사람용 안내문을 찍는데, MCP 규약상 stdout 은 JSON 전용이라
    클라이언트가 그 줄을 읽으려다 실패하며 긴 트레이스백을 남긴다. 동작에는 문제가 없다.
    """
    logging.getLogger("mcp.client.stdio").setLevel(logging.CRITICAL)


def load_api_key(day_dir: Path) -> None:
    """일차 폴더와 실습자료 루트의 .env 를 읽어 OPENAI_API_KEY 가 있는지 확인한다.

    모델을 부르는 파일에서 맨 앞에 부른다. 중간에 멈추면 어디까지 됐는지 헷갈린다.
    """
    load_dotenv(day_dir / ".env")           # 일차 폴더의 .env
    load_dotenv(day_dir.parent / ".env")    # 실습자료 루트의 .env
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY 를 찾지 못했습니다. 일차 폴더에서 `cp .env.example .env` 후 키를 채우세요.")


def chinook_db_path(data_dir: Path) -> Path:
    """data 폴더의 샘플 DB(chinook.db) 경로를 돌려준다. 없으면 그 자리에서 멈춘다.

    DB 가 없어도 SQLite 서버는 빈 DB 를 열고 에러를 예외가 아닌 평범한 문자열로 돌려준다.
    모델이 그것을 결과로 착각하므로, 엉뚱한 답으로 드러나기 전에 여기서 끊는다.
    """
    db_path = data_dir / "chinook.db"
    if not db_path.exists():
        raise SystemExit(f"{db_path} 가 없습니다. 배포본의 data 폴더를 그대로 두었는지 확인하세요.")
    print(f"chinook DB 준비됨: {db_path.name} ({db_path.stat().st_size // 1024}KB)")
    return db_path


def child_env() -> dict[str, str]:
    """코드 실행 서버에 넘길 환경 변수를 만든다.

    서버는 'python' 을 PATH 에서 찾는데 맥에는 python3 만 있는 경우가 많아, 지금 가상환경의
    실행 파일 폴더를 PATH 맨 앞에 붙인다. PATH 하나면 된다. HOME 같은 나머지는 MCP 클라이언트가
    알아서 물려준다(mcp.client.stdio 의 get_default_environment). os.environ 을 통째로 넘기면
    셸 프롬프트(PS1) 같은 것까지 딸려가 경고가 뜬다.
    """
    return {"PATH": str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")}


def block_text(result: str | list[str | dict[str, Any]]) -> str:
    """MCP 도구가 돌려준 값에서 사람이 읽을 문자열을 뽑는다.

    모양이 셋이라 전부 받는다. 하나만 가정하면 에러가 났을 때 엉뚱한 곳에서 TypeError 로 터진다.
      1) 콘텐츠 블록 리스트  [{'type': 'text', 'text': '...'}]   <- 보통 이 모양
      2) 문자열 리스트       ['...']
      3) 그냥 문자열         '...'                              <- 서버가 에러를 낼 때
    """
    if isinstance(result, str):
        return result
    if isinstance(result, list):
        return "\n".join(b if isinstance(b, str) else b.get("text", "") for b in result)
    return str(result)


def one_line(value: Any, limit: int = 90) -> str:
    """줄바꿈과 연속 공백을 한 칸으로 눌러 한 줄로 만들고, 길면 앞부분만 남긴다."""
    text = " ".join(str(value).split())
    return text if len(text) <= limit else f"{text[:limit]}... ({len(text)}자)"


def print_trajectory(result: dict[str, Any], width: int = 90) -> None:
    """에이전트가 어떤 도구를 어떤 인자로 불렀는지와 최종 답을 찍는다.

    코드나 SQL 은 길고 줄바꿈이 많아 그대로 찍으면 화면을 덮는다. 한 줄로 눌러 앞부분만 보이고,
    잘린 것은 원래 길이를 함께 적는다. 무엇을 몇 번째로 불렀는지 보는 것이 목적이라 이 정도면 된다.
    """
    step = 0
    for message in result["messages"]:
        if isinstance(message, AIMessage) and message.tool_calls:
            for call in message.tool_calls:
                step += 1
                print(f"[{step:>2}] {call['name']}")
                for key, value in call["args"].items():
                    print(f"     - {key} = {one_line(value, width)}")
        elif isinstance(message, ToolMessage):
            # 한글 라벨은 터미널에서 두 칸을 차지해 자릿수를 맞춰도 어긋난다. 그래서 기호로 구분한다.
            print(f"     > {one_line(block_text(message.content), width)}")

    print()
    print("최종 답")
    print("-" * 60)
    print(result["messages"][-1].text.strip())


def tool_names(result: dict[str, Any]) -> list[str]:
    """호출된 도구 이름만 순서대로 돌려준다(확인용).

    print_trajectory 가 인자와 결과까지 찍는다면, 이쪽은 '무엇을 몇 개 불렀나' 만 한 줄로 본다.
    """
    return [call["name"] for message in result["messages"]
            if isinstance(message, AIMessage) and message.tool_calls
            for call in message.tool_calls]


def result_value(blocks: str | list[str | dict[str, Any]]) -> str:
    """browser_evaluate 결과에서 '### Result' 아래의 값만 꺼낸다.

    이 서버는 값만 주지 않고 실행한 Playwright 코드까지 함께 돌려준다.
    """
    text = block_text(blocks)
    return text.split("### Result", 1)[-1].split("### Ran Playwright code", 1)[0].strip()


def extract_code(answer: str) -> str:
    """모델 답변에서 첫 코드블록의 코드만 꺼낸다. 코드블록이 없으면 답변을 그대로 돌려준다."""
    if "```" not in answer:
        return answer.strip()
    block = answer.split("```", 2)[1]
    if block.startswith("python"):
        block = block[len("python"):]
    return block.strip()
