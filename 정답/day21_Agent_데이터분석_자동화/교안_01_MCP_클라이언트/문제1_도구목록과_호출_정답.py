"""📝 과제 문제 1 정답: 파일시스템 서버에 붙어 도구 목록·명세를 보고 직접 호출하기

준비물: npx(Node.js)
실행: 이 파일이 있는 폴더에서  uv run 문제1_도구목록과_호출_정답.py
"""

import asyncio
import sys
from pathlib import Path

# 실습 폴더의 과제 파일들이 함께 쓰는 공통.py 를 그대로 씁니다
sys.path.append(str(Path(__file__).resolve().parents[3] / "day21_Agent_데이터분석_자동화" / "교안_01_MCP_클라이언트" / "과제"))

from langchain_mcp_adapters.client import MultiServerMCPClient

from 공통 import DATA_DIR, FILESYSTEM


async def main():
    # 문제 1. 파일시스템 서버에 붙어 도구 목록·명세를 보고 직접 호출하기
    fs_tools = await MultiServerMCPClient({"files": FILESYSTEM}).get_tools()
    fs_by_name = {t.name: t for t in fs_tools}
    list_dir_args = list(fs_by_name["list_directory"].args)
    data_listing = (await fs_by_name["list_directory"].ainvoke({"path": str(DATA_DIR)}))[0]["text"]

    # [자가채점]
    assert len(fs_tools) >= 10, f"도구가 너무 적습니다: {len(fs_tools)}개"
    assert "list_directory" in fs_by_name, "list_directory 도구가 없습니다"
    assert list_dir_args == ["path"], f"인자 이름이 다릅니다: {list_dir_args}"
    assert isinstance(data_listing, str) and "cvs_sales.csv" in data_listing, "data 폴더 목록이 아닙니다"
    print("문제 1 통과 -- 도구", len(fs_tools), "개 · 인자:", list_dir_args)


if __name__ == "__main__":
    asyncio.run(main())
