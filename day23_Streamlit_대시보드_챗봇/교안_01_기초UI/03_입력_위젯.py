# 실행: uv run streamlit run 교안_01_기초UI/03_입력_위젯.py
#
# 교안 01: 사용자 입력 위젯
# 위젯은 화면에 입력칸을 그리고, 사용자가 넣은 값을 '반환'합니다.
# 위젯을 조작하면 스크립트가 재실행되고, 위젯은 최신 값을 다시 돌려줍니다.

import os

# [제공 코드] pandas/Streamlit 이 쓰는 Arrow 의 메모리 할당기를 표준(system)으로 고정.
# 기본 할당기(mimalloc)는 macOS 에서 화면 재실행 시 앱이 죽는 문제가 있어 미리 막아 둔다.
# 반드시 pandas 를 import 하기 전에 설정해야 효과가 있다.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

from datetime import date

import pandas as pd
import streamlit as st

st.title("📗 입력 위젯")
st.caption("텍스트·숫자·선택·버튼: 사용자와 상호작용하는 기본 요소")

st.divider()

# =============================================================================
st.header("1. 텍스트 입력: text_input, text_area")
st.markdown("한 줄 입력은 `text_input`, 여러 줄은 `text_area`. 반환값은 사용자가 입력한 문자열입니다.")

st.code(
    '''name = st.text_input("이름을 입력하세요", placeholder="홍길동")
intro = st.text_area("자기소개", height=100)

if name:
    st.write(f"안녕하세요, {name}님!")
if intro:
    st.write(f"자기소개 {len(intro)}자 · {len(intro.splitlines())}줄")
    st.text(intro)          # st.write 와 달리 줄바꿈을 그대로 살려 보여 준다''',
    language="python",
)
st.caption("▼ 실제 실행 결과: 이름과 자기소개를 입력하면 아래에 그대로 나옵니다")
name = st.text_input("이름을 입력하세요", placeholder="홍길동")
intro = st.text_area("자기소개", height=100)

if name:
    st.write(f"안녕하세요, {name}님!")
if intro:
    # 두 위젯의 차이를 눈으로 확인하는 자리다. text_area 는 줄바꿈이 그대로 담긴다.
    st.write(f"자기소개 {len(intro)}자 · {len(intro.splitlines())}줄")
    # st.write 로 찍으면 마크다운으로 해석돼 줄바꿈이 합쳐진다. 입력 그대로 보려면 st.text.
    st.text(intro)

st.divider()

# =============================================================================
st.header("2. 숫자·슬라이더: number_input, slider")
st.markdown("정확한 숫자는 `number_input`, 범위에서 고르는 느낌은 `slider`. 슬라이더는 튜플을 주면 **범위** 선택이 됩니다.")

st.code(
    '''age = st.number_input("나이", min_value=0, max_value=120, value=25, step=1)
price_range = st.slider("가격 범위", 0, 100000, (20000, 60000), step=5000)
st.write(f"나이 {age}세 · 가격 {price_range[0]:,}~{price_range[1]:,}원")''',
    language="python",
)
st.caption("▼ 실제 실행 결과")
age = st.number_input("나이", min_value=0, max_value=120, value=25, step=1)
price_range = st.slider("가격 범위", 0, 100000, (20000, 60000), step=5000)
st.write(f"나이 {age}세 · 가격 {price_range[0]:,}~{price_range[1]:,}원")

st.divider()

# =============================================================================
st.header("3. 선택: selectbox, multiselect, radio")
st.markdown(
    """
- `selectbox` : 드롭다운에서 **하나** 선택
- `multiselect` : **여러 개** 선택(리스트 반환)
- `radio` : 모든 선택지를 펼쳐 놓고 **하나** 선택
"""
)

st.code(
    '''city = st.selectbox("도시", ["서울", "부산", "대구"])
tags = st.multiselect("관심사", ["AI", "데이터", "웹", "게임"], default=["AI"])
plan = st.radio("요금제", ["무료", "프로"], horizontal=True)
st.write(f"{city} · {tags} · {plan}")''',
    language="python",
)
st.caption("▼ 실제 실행 결과")
city = st.selectbox("도시", ["서울", "부산", "대구"])
tags = st.multiselect("관심사", ["AI", "데이터", "웹", "게임"], default=["AI"])
plan = st.radio("요금제", ["무료", "프로"], horizontal=True)
st.write(f"{city} · {tags} · {plan}")

# 🖐️ 직접 해보기: multiselect 의 선택지를 바꾸고, 몇 개를 골랐는지 len 으로 세어 출력해 보세요.

st.divider()

# =============================================================================
st.header("4. 예/아니오·버튼: checkbox, toggle, button")
st.markdown(
    "`checkbox`·`toggle` 은 True/False 를 반환합니다. `button` 은 **눌린 그 순간의 재실행에서만** True 입니다."
)

st.code(
    '''agree = st.checkbox("약관에 동의합니다")
dark = st.toggle("다크 모드")
if st.button("제출", type="primary"):
    st.success("제출되었습니다!")
st.write(f"동의={agree}, 다크모드={dark}")''',
    language="python",
)
st.caption("▼ 실제 실행 결과")
agree = st.checkbox("약관에 동의합니다")
dark = st.toggle("다크 모드")
if st.button("제출", type="primary"):
    st.success("제출되었습니다!")
st.write(f"동의={agree}, 다크모드={dark}")

st.warning(
    "주의: `st.button` 은 눌린 직후 한 번의 재실행에서만 True 입니다. "
    "값을 계속 기억하려면 `st.session_state` 를 씁니다(교안 05)."
)

st.divider()

# =============================================================================
st.header("5. 날짜·파일·색: date_input, file_uploader, color_picker")
st.markdown(
    """
대시보드에서 자주 쓰는 나머지 세 가지입니다.

- `date_input` : 날짜를 고릅니다. 튜플을 주면 **기간(시작~끝)** 선택이 됩니다(기간 필터에 씁니다).
- `file_uploader` : 사용자가 올린 파일을 받습니다. **아무것도 안 올렸으면 `None`** 이라, 반드시 먼저 확인해야 합니다.
- `color_picker` : 색을 골라 `"#RRGGBB"` 문자열로 돌려줍니다(그래프 색을 사용자가 바꾸게 할 때).
"""
)

st.code(
    '''period = st.date_input("조회 기간", value=(date(2024, 1, 1), date(2024, 3, 31)))
color = st.color_picker("강조 색", value="#5B8DEF")

up = st.file_uploader("CSV 올리기", type=["csv"])
if up is not None:                      # 안 올렸으면 None 이므로 먼저 확인한다
    user_df = pd.read_csv(up)           # 업로드된 객체를 그대로 read_csv 에 넘길 수 있다
    st.write(f"{up.name} · {len(user_df)}행")
    st.dataframe(user_df.head(), width="stretch")
else:
    st.caption("아직 올린 파일이 없습니다.")''',
    language="python",
)
st.caption("▼ 실제 실행 결과 (파일은 올리지 않아도 아래 문구가 뜹니다)")

# 기간 필터용 date_input: value 에 (시작, 끝) 튜플을 주면 기간 선택 위젯이 된다
period = st.date_input("조회 기간", value=(date(2024, 1, 1), date(2024, 3, 31)))
color = st.color_picker("강조 색", value="#5B8DEF")
st.write(f"기간 {period} · 색 `{color}`")

up = st.file_uploader("CSV 올리기", type=["csv"])
if up is not None:
    # 업로드된 파일 객체는 파일처럼 읽을 수 있어 read_csv 에 바로 넘어간다
    user_df = pd.read_csv(up)
    st.write(f"{up.name} · {len(user_df)}행")
    st.dataframe(user_df.head(), width="stretch")
else:
    st.caption("아직 올린 파일이 없습니다.")

# 🖐️ 직접 해보기: date_input 의 value 에서 튜플을 없애고 date(2024, 1, 1) 하나만 주세요.
#               위젯이 기간 선택에서 날짜 하나 선택으로 바뀝니다. 확인했으면 되돌리세요.

st.info(
    "`file_uploader` 는 값이 `None` 일 수 있는 유일한 위젯 축에 듭니다. "
    "`if up is not None:` 를 빼면 파일을 올리기 전에 앱이 에러로 멈춥니다."
)

st.divider()
st.subheader("이번 강의 정리")
st.markdown(
    """
- 위젯은 화면에 입력칸을 그리고 **입력값을 반환**한다
- 텍스트(`text_input`/`text_area`), 숫자(`number_input`/`slider`)
- 선택(`selectbox`/`multiselect`/`radio`), 참/거짓(`checkbox`/`toggle`), 액션(`button`)
- 날짜·파일·색(`date_input`/`file_uploader`/`color_picker`), 업로드는 **None 검사 먼저**
- `button` 은 눌린 순간에만 True. 상태 유지는 다음 시간에
"""
)
st.markdown("⏭️ **다음 시간**: 레이아웃과 차트 (`교안_01_기초UI/04_레이아웃과_차트.py`)")
