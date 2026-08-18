# 실행: uv run streamlit run 교안_01_기초UI/01_시작하기.py
#
# 교안 01: Streamlit 시작하기
# 이 파일은 "읽고 실행하는" 교안입니다. 왼쪽 코드(st.code)와 바로 아래 실제 결과를
# 나란히 보면서, 각 명령이 화면에 무엇을 그리는지 눈으로 익히세요.

import os

# [제공 코드] pandas/Streamlit 이 쓰는 Arrow 의 메모리 할당기를 표준(system)으로 고정.
# 기본 할당기(mimalloc)는 macOS 에서 화면 재실행 시 앱이 죽는 문제가 있어 미리 막아 둔다.
# 반드시 pandas 를 import 하기 전에 설정해야 효과가 있다.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import streamlit as st

st.title("📗 Streamlit 시작하기")
st.caption("데이터 스크립트를 몇 줄로 웹 앱으로 바꾸는 파이썬 프레임워크")

st.markdown(
    """
**오늘의 목표**
- [ ] Streamlit이 무엇이고 왜 쓰는지 이해한다
- [ ] `uv run streamlit run` 으로 앱을 실행하고 `Ctrl` + `C` 로 종료한다
- [ ] "스크립트 재실행" 모델을 이해한다
- [ ] 텍스트 출력 명령(`write`, `title`, `markdown` 등)을 쓴다
"""
)

st.divider()

# =============================================================================
st.header("1. Streamlit이란?")
st.markdown(
    """
지금까지는 분석 결과를 노트북 안에서만 봤습니다. **Streamlit**은 그 파이썬 코드를
**웹 앱**으로 바꿔, 누구나 브라우저에서 클릭·입력하며 쓸 수 있게 해 줍니다.

- HTML·CSS·자바스크립트를 몰라도 **파이썬만으로** UI를 만든다.
- `st.무언가(...)` 를 부르면 그 요소가 화면에 **위에서 아래로** 쌓인다.
- 대화형 AI 챗봇, 데이터 분석 대시보드를 빠르게 만들 때 특히 강력하다.

**실행 방법**(터미널):
"""
)
st.code("uv run streamlit run 교안_01_기초UI/01_시작하기.py", language="bash")
st.markdown("실행하면 브라우저가 열리고, 코드를 저장할 때마다 오른쪽 위 **Rerun** 으로 갱신됩니다.")

st.markdown("**끄는 방법**: 앱은 터미널에서 계속 돌고 있습니다. 실행한 그 터미널에서 `Ctrl` + `C` 를 누르면 멈춥니다.")
st.code("Ctrl + C          # 앱 종료 (macOS 도 Command 가 아니라 Control 이다)", language="bash")
st.info(
    "브라우저 탭만 닫으면 앱은 계속 돌아갑니다. 끄지 않은 채 다시 실행하면 "
    "포트가 이미 쓰이고 있어 8502, 8503 처럼 다른 주소로 열립니다. "
    "그때는 앞서 띄운 터미널에서 `Ctrl` + `C` 로 정리하세요."
)

st.divider()

# =============================================================================
st.header("2. st.write: 만능 출력")
st.markdown("`st.write()` 는 문자열·숫자·리스트·딕셔너리·DataFrame 등 **무엇이든** 알아서 예쁘게 출력합니다.")

# ▼ 화면에 코드를 명시하고(st.code), 바로 아래에서 같은 코드를 실제로 실행합니다.
st.code(
    '''st.write("안녕하세요, Streamlit!")
st.write("숫자와 계산도:", 3 * 7)
st.write(["사과", "바나나", "포도"])''',
    language="python",
)
st.caption("▼ 위 코드의 실제 실행 결과")
st.write("안녕하세요, Streamlit!")
st.write("숫자와 계산도:", 3 * 7)
st.write(["사과", "바나나", "포도"])

# 🖐️ 직접 해보기: 위 st.write 에 여러분의 이름과 좋아하는 숫자를 넣어 출력해 보세요.

st.divider()

# =============================================================================
st.header("3. 제목·소제목: title, header, subheader")
st.markdown("문서처럼 **계층 있는 제목**으로 화면을 구조화합니다.")

st.code(
    '''st.title("가장 큰 제목")
st.header("중간 제목")
st.subheader("작은 제목")
st.caption("회색 보조 설명")''',
    language="python",
)
st.caption("▼ 실제 실행 결과")
st.title("가장 큰 제목")
st.header("중간 제목")
st.subheader("작은 제목")
st.caption("회색 보조 설명")

st.divider()

# =============================================================================
st.header("4. 마크다운·텍스트: markdown, text, code")
st.markdown(
    "`st.markdown` 은 **굵게**·*기울임*·목록·링크 같은 마크다운 문법을 지원하고, "
    "`st.code` 는 코드 블록을, `st.text` 는 서식 없는 그대로의 글자를 보여 줍니다."
)

st.code(
    '''st.markdown("**굵게**, *기울임*, `코드조각`")
st.markdown("- 목록 1\\n- 목록 2")
st.text("서식 없는 그대로의 텍스트\\n줄바꿈도 유지됩니다")''',
    language="python",
)
st.caption("▼ 실제 실행 결과")
st.markdown("**굵게**, *기울임*, `코드조각`")
st.markdown("- 목록 1\n- 목록 2")
st.text("서식 없는 그대로의 텍스트\n줄바꿈도 유지됩니다")

# 🖐️ 직접 해보기: st.markdown 으로 좋아하는 사이트 링크를 [이름](주소) 형식으로 만들어 보세요.

st.divider()

# =============================================================================
st.header("5. 핵심 개념: '스크립트 재실행(rerun)' 모델")
st.markdown(
    """
Streamlit의 가장 중요한 원리입니다.

> **위젯을 조작할 때마다, Streamlit은 이 파이썬 스크립트를 처음부터 끝까지 다시 실행합니다.**

아래 슬라이더를 움직여 보세요. 값을 바꿀 때마다 스크립트가 다시 돌면서 결과 문장이 새로 그려집니다.
"""
)
st.code(
    '''number = st.slider("숫자를 고르세요", 0, 100, 25)
st.write(f"선택한 값의 제곱은 {number ** 2} 입니다.")''',
    language="python",
)
st.caption("▼ 실제 실행 결과: 슬라이더를 움직이면 스크립트가 재실행됩니다")
number = st.slider("숫자를 고르세요", 0, 100, 25)
st.write(f"선택한 값의 제곱은 {number ** 2} 입니다.")

st.divider()
st.subheader("이번 강의 정리")
st.markdown(
    """
- Streamlit = 파이썬만으로 웹 앱(대시보드·챗봇)을 만드는 도구, `uv run streamlit run` 으로 실행하고 `Ctrl` + `C` 로 종료
- `st.write` 는 만능 출력, `st.title/header/subheader/caption` 으로 구조화
- `st.markdown/text/code` 로 서식 있는/없는 텍스트·코드 표시
- **재실행 모델**: 위젯 조작 → 스크립트 전체 재실행
"""
)
st.markdown("⏭️ **다음 시간**: 데이터를 표·지표로 보여 주기 (`교안_01_기초UI/02_데이터_표시.py`)")
